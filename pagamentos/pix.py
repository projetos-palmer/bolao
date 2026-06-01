import io
import base64
import uuid
from django.utils import timezone
from datetime import timedelta

import qrcode


def gerar_payload_pix(chave: str, nome: str, cidade: str, valor: float, txid: str = '') -> str:
    """
    Gera o payload do Pix (formato EMV) para copia e cola.
    Implementação simplificada para MVP.
    """
    def campo(id_campo: str, valor_campo: str) -> str:
        tamanho = str(len(valor_campo)).zfill(2)
        return f'{id_campo}{tamanho}{valor_campo}'

    merchant_account = campo('00', 'BR.GOV.BCB.PIX') + campo('01', chave)
    payload = (
        campo('00', '01')
        + campo('26', merchant_account)
        + campo('52', '0000')
        + campo('53', '986')
        + campo('54', f'{valor:.2f}')
        + campo('58', 'BR')
        + campo('59', nome[:25])
        + campo('60', cidade[:15])
        + campo('62', campo('05', txid[:25] if txid else '***'))
    )

    # CRC16
    payload += '6304'
    crc = _crc16(payload)
    return payload + crc


def _crc16(dados: str) -> str:
    polinomio = 0x1021
    resultado = 0xFFFF
    for byte in dados.encode('utf-8'):
        resultado ^= byte << 8
        for _ in range(8):
            if resultado & 0x8000:
                resultado = (resultado << 1) ^ polinomio
            else:
                resultado <<= 1
            resultado &= 0xFFFF
    return format(resultado, '04X')


def gerar_qr_code_base64(payload: str) -> str:
    """Gera QR Code como string base64 PNG."""
    img = qrcode.make(payload)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


# ---------------------------------------------------------------------------
# Integração EFI Bank (ex-Gerencianet) — confirmação automática via API PIX
# ---------------------------------------------------------------------------

def tem_credenciais_efi(config_pix) -> bool:
    """Verifica se as credenciais EFI Bank estão completamente preenchidas."""
    return bool(
        config_pix.client_id_efi
        and config_pix.client_secret_efi
        and config_pix.certificado_efi
    )


def _get_efi_client(config_pix):
    """Cria instância autenticada do cliente EFI Bank."""
    from efipay import EfiPay
    credentials = {
        'client_id': config_pix.client_id_efi,
        'client_secret': config_pix.client_secret_efi,
        'certificate': config_pix.certificado_efi.path,
        'sandbox': config_pix.ambiente_efi == 'homologacao',
    }
    return EfiPay(credentials)


def criar_cobranca_efi(config_pix, valor: float, txid: str) -> dict:
    """
    Cria cobrança PIX via EFI Bank (cobrança imediata com txid definido).
    Retorna o dict de resposta da API (contém 'pixCopiaECola').
    """
    efi = _get_efi_client(config_pix)
    body = {
        'calendario': {'expiracao': 300},
        'valor': {'original': f'{valor:.2f}'},
        'chave': config_pix.chave_pix,
        'infoAdicionais': [
            {'nome': 'Sistema', 'valor': 'Bolao Copa do Mundo'}
        ],
    }
    params = {'txid': txid}
    return efi.pix_create_charge(params=params, body=body)


def registrar_webhook_efi(config_pix, webhook_url: str) -> dict:
    """Registra a URL de webhook no EFI Bank para notificações de PIX recebidos."""
    efi = _get_efi_client(config_pix)
    body = {'webhookUrl': webhook_url}
    params = {'chave': config_pix.chave_pix}
    return efi.pix_config_webhook(params=params, body=body)


def enviar_premio_pix(config_pix, chave_destino: str, valor: float, id_envio: str, descricao: str = '') -> dict:
    """
    Envia um PIX para a chave do ganhador via EFI Bank.
    - config_pix: ConfiguracaoPixAdministrador com credenciais EFI
    - chave_destino: chave PIX do ganhador (CPF, e-mail, telefone ou aleatória)
    - valor: valor em float (ex: 25.50)
    - id_envio: identificador único do envio (UUID sem hífens, máx 35 chars)
    - descricao: mensagem opcional para o favorecido
    Retorna o dict de resposta da API.
    """
    efi = _get_efi_client(config_pix)
    params = {'idEnvio': id_envio[:35]}
    body = {
        'valor': f'{valor:.2f}',
        'pagador': {
            'chave': config_pix.chave_pix,
            'infoPagador': descricao[:140] if descricao else 'Premio Bolao Copa do Mundo',
        },
        'favorecido': {
            'chave': chave_destino,
        },
    }
    return efi.pix_send(params=params, body=body)


# ---------------------------------------------------------------------------
# Criação de pagamento (usa EFI Bank se configurado, senão QR estático)
# ---------------------------------------------------------------------------

def criar_pagamento(participacao, config_pix):
    """
    Cria um Pagamento para a participação.
    - Se credenciais EFI Bank estiverem configuradas: cria cobrança real via API
      e o sistema confirma automaticamente via webhook quando o PIX for recebido.
    - Caso contrário: gera QR Code estático (requer confirmação manual pelo admin).
    Retorna o objeto Pagamento criado.
    """
    from .models import Pagamento

    valor = float(participacao.bolao.valor_participacao)
    # txid para EFI Bank: 26-35 chars alfanuméricos (UUID sem hífens = 32 chars)
    txid_efi = str(participacao.codigo_identificador).replace('-', '')
    # txid para QR estático: máx 25 chars (limitação EMV)
    txid_estatico = txid_efi[:25]

    if tem_credenciais_efi(config_pix):
        try:
            resposta = criar_cobranca_efi(config_pix, valor, txid_efi)
            pix_copia_cola = resposta.get('pixCopiaECola', '')
            if not pix_copia_cola:
                raise ValueError('Resposta EFI sem pixCopiaECola')
            qr_base64 = gerar_qr_code_base64(pix_copia_cola)
            data_expiracao = timezone.now() + timedelta(seconds=300)
            txid_final = txid_efi
        except Exception:
            # Fallback: QR estático caso a API EFI falhe
            pix_copia_cola = gerar_payload_pix(
                chave=config_pix.chave_pix,
                nome=config_pix.nome_recebedor,
                cidade='Brasil',
                valor=valor,
                txid=txid_estatico,
            )
            qr_base64 = gerar_qr_code_base64(pix_copia_cola)
            data_expiracao = timezone.now() + timedelta(seconds=300)
            txid_final = txid_estatico
    else:
        # QR estático sem integração bancária (confirmação manual)
        pix_copia_cola = gerar_payload_pix(
            chave=config_pix.chave_pix,
            nome=config_pix.nome_recebedor,
            cidade='Brasil',
            valor=valor,
            txid=txid_estatico,
        )
        qr_base64 = gerar_qr_code_base64(pix_copia_cola)
        data_expiracao = timezone.now() + timedelta(seconds=300)
        txid_final = txid_estatico

    pagamento = Pagamento.objects.create(
        participacao=participacao,
        valor=participacao.bolao.valor_participacao,
        txid=txid_final,
        qr_code=qr_base64,
        pix_copia_cola=pix_copia_cola,
        data_expiracao=data_expiracao,
    )
    return pagamento


# ---------------------------------------------------------------------------
# Pagamento em lote — um único PIX quita várias participações
# ---------------------------------------------------------------------------

def criar_pagamento_lote(participacoes, config_pix, usuario):
    """
    Cria um PagamentoLote (um único QR Code / PIX copia-e-cola) para quitar
    todas as participações listadas.
    Também cria os Pagamento individuais vinculados ao lote.
    Retorna o objeto PagamentoLote criado.
    """
    from .models import Pagamento, PagamentoLote

    valor_total = sum(float(p.bolao.valor_participacao) for p in participacoes)

    # txid do lote: UUID sem hífens (32 chars) — prefixado com 'L' para não
    # colidir com txids individuais
    txid_lote_raw = 'L' + uuid.uuid4().hex[:31]  # 32 chars

    if tem_credenciais_efi(config_pix):
        try:
            resposta = criar_cobranca_efi(config_pix, valor_total, txid_lote_raw)
            pix_copia_cola = resposta.get('pixCopiaECola', '')
            if not pix_copia_cola:
                raise ValueError('Resposta EFI sem pixCopiaECola')
            qr_base64 = gerar_qr_code_base64(pix_copia_cola)
            data_expiracao = timezone.now() + timedelta(seconds=300)
            txid_final = txid_lote_raw
        except Exception:
            txid_estatico = txid_lote_raw[:25]
            pix_copia_cola = gerar_payload_pix(
                chave=config_pix.chave_pix,
                nome=config_pix.nome_recebedor,
                cidade='Brasil',
                valor=valor_total,
                txid=txid_estatico,
            )
            qr_base64 = gerar_qr_code_base64(pix_copia_cola)
            data_expiracao = timezone.now() + timedelta(seconds=300)
            txid_final = txid_estatico
    else:
        txid_estatico = txid_lote_raw[:25]
        pix_copia_cola = gerar_payload_pix(
            chave=config_pix.chave_pix,
            nome=config_pix.nome_recebedor,
            cidade='Brasil',
            valor=valor_total,
            txid=txid_estatico,
        )
        qr_base64 = gerar_qr_code_base64(pix_copia_cola)
        data_expiracao = timezone.now() + timedelta(seconds=300)
        txid_final = txid_estatico

    lote = PagamentoLote.objects.create(
        usuario=usuario,
        valor_total=valor_total,
        txid=txid_final,
        qr_code=qr_base64,
        pix_copia_cola=pix_copia_cola,
        data_expiracao=data_expiracao,
    )

    for participacao in participacoes:
        # Cria Pagamento individual vinculado ao lote (sem txid próprio — o lote é o txid)
        Pagamento.objects.get_or_create(
            participacao=participacao,
            defaults={
                'lote': lote,
                'valor': participacao.bolao.valor_participacao,
                'txid': '',  # pago via lote
                'qr_code': '',
                'pix_copia_cola': '',
                'data_expiracao': data_expiracao,
            }
        )

    return lote

