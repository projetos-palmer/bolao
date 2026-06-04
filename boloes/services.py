from django.utils import timezone
from decimal import Decimal
import uuid
import logging

from .models import Bolao, ParticipacaoBolao, Premio

logger = logging.getLogger(__name__)


def calcular_ganhadores(bolao: Bolao):
    """
    Calcula os ganhadores de um bolão após o resultado ser informado.
    Divide o prêmio igualmente entre os acertadores do placar exato.
    Pode ser chamado múltiplas vezes (recalcula limpando premios anteriores).
    """
    jogo = bolao.jogo
    if not jogo.resultado_definido:
        return []

    # Aceita re-execução: inclui statuses de cálculos anteriores
    participacoes_pagas = bolao.participacoes.filter(
        status__in=['confirmado', 'valido', 'nao_premiado', 'vencedor']
    )

    # Limpa prêmios anteriores para recalcular corretamente
    Premio.objects.filter(bolao=bolao).delete()

    ganhadores = [p for p in participacoes_pagas if p.acertou_placar]

    # Marca todas como não premiadas primeiro
    participacoes_pagas.update(status='nao_premiado')

    if not ganhadores:
        bolao.status = 'premiacao'
        bolao.save(update_fields=['status'])
        return []

    valor_total = bolao.valor_total_premio
    valor_por_ganhador = Decimal(str(valor_total)) / len(ganhadores)

    premios_criados = []
    for participacao in ganhadores:
        participacao.status = 'vencedor'
        participacao.save(update_fields=['status'])

        premio, criado = Premio.objects.get_or_create(
            bolao=bolao,
            usuario=participacao.usuario,
            participacao=participacao,
            defaults={'valor': valor_por_ganhador},
        )
        if not criado:
            premio.valor = valor_por_ganhador
            premio.save(update_fields=['valor'])
        premios_criados.append(premio)

    bolao.status = 'premiacao'
    bolao.save(update_fields=['status'])

    return premios_criados


def verificar_boloes_para_fechar():
    """Fecha bolões cujo limite de aposta (5min antes) já passou."""
    agora = timezone.now()
    boloes_abertos = Bolao.objects.filter(status='aberto').select_related('jogo')
    for bolao in boloes_abertos:
        if agora >= bolao.jogo.limite_aposta:
            bolao.status = 'fechado'
            bolao.save(update_fields=['status'])


def pagar_premios_bolao(bolao: Bolao) -> dict:
    """
    Paga ou registra o pagamento dos premios dos ganhadores.

    - EFI Bank configurado: envia PIX automaticamente via API EFI.
    - Apenas Mercado Pago configurado: registra pagamento manual feito pelo
      administrador no app/conta Mercado Pago.

    Retorna um dict com:
      - modo: efi_automatico ou mercado_pago_manual
      - pagos: lista de dicts dos premios pagos/registrados com sucesso
      - falhos: lista de dicts dos premios que falharam
      - sem_pix: lista de ganhadores sem chave PIX cadastrada
    """
    from pagamentos.models import ConfiguracaoPixAdministrador
    from pagamentos.pix import enviar_premio_pix, tem_credenciais_efi
    from pagamentos.pix_mp import tem_credenciais_mp

    config_pix = ConfiguracaoPixAdministrador.objects.filter(ativo=True).first()
    usar_efi = tem_credenciais_efi(config_pix) if config_pix else False
    usar_mp_manual = tem_credenciais_mp(config_pix) if config_pix else False

    if not usar_efi and not usar_mp_manual:
        raise ValueError('Configure Mercado Pago ou EFI Bank em Painel > Configuracao Pix.')

    premios_pendentes = Premio.objects.filter(
        bolao=bolao,
        status_pagamento='pendente',
    ).select_related('usuario', 'participacao', 'usuario__pix')

    pagos = []
    falhos = []
    sem_pix = []

    for premio in premios_pendentes:
        usuario = premio.usuario
        pix_usuario = getattr(usuario, 'pix', None)

        if not pix_usuario or not pix_usuario.chave_pix:
            sem_pix.append({'usuario': usuario.nome_completo, 'valor': float(premio.valor)})
            continue

        if usar_mp_manual:
            premio.status_pagamento = 'pago'
            premio.data_pagamento = timezone.now()
            premio.comprovante = (
                'Pagamento manual via Mercado Pago confirmado pelo administrador. '
                f'Chave PIX: {pix_usuario.chave_pix}; Valor: R$ {premio.valor}'
            )
            premio.save(update_fields=['status_pagamento', 'data_pagamento', 'comprovante'])

            premio.participacao.status = 'premio_pago'
            premio.participacao.save(update_fields=['status'])

            pagos.append({'usuario': usuario.nome_completo, 'valor': float(premio.valor)})
            logger.info(
                'Premio PIX registrado manualmente via Mercado Pago: usuario=%s valor=%s',
                usuario.nome_completo,
                premio.valor,
            )
            continue

        id_envio = str(uuid.uuid4()).replace('-', '')[:35]
        descricao = f'Premio Bolao {bolao.nome}'[:140]

        try:
            resposta = enviar_premio_pix(
                config_pix=config_pix,
                chave_destino=pix_usuario.chave_pix,
                valor=float(premio.valor),
                id_envio=id_envio,
                descricao=descricao,
            )

            if isinstance(resposta, dict) and resposta.get('idEnvio'):
                premio.status_pagamento = 'pago'
                premio.data_pagamento = timezone.now()
                premio.comprovante = str(resposta)
                premio.save(update_fields=['status_pagamento', 'data_pagamento', 'comprovante'])

                premio.participacao.status = 'premio_pago'
                premio.participacao.save(update_fields=['status'])

                pagos.append({'usuario': usuario.nome_completo, 'valor': float(premio.valor)})
                logger.info('Premio PIX enviado: usuario=%s valor=%s idEnvio=%s', usuario.nome_completo, premio.valor, id_envio)
            else:
                premio.status_pagamento = 'falhou'
                premio.comprovante = str(resposta)
                premio.save(update_fields=['status_pagamento', 'comprovante'])
                falhos.append({'usuario': usuario.nome_completo, 'valor': float(premio.valor), 'erro': str(resposta)})
                logger.warning('Falha ao enviar premio PIX: usuario=%s resposta=%s', usuario.nome_completo, resposta)

        except Exception as exc:
            premio.status_pagamento = 'falhou'
            premio.comprovante = str(exc)
            premio.save(update_fields=['status_pagamento', 'comprovante'])
            falhos.append({'usuario': usuario.nome_completo, 'valor': float(premio.valor), 'erro': str(exc)})
            logger.exception('Erro ao enviar premio PIX para %s', usuario.nome_completo)

    ainda_pendentes = Premio.objects.filter(bolao=bolao, status_pagamento='pendente').exists()
    if not ainda_pendentes and (pagos or not falhos):
        bolao.status = 'pago'
        bolao.save(update_fields=['status'])

    modo = 'efi_automatico' if usar_efi else 'mercado_pago_manual'
    return {'modo': modo, 'pagos': pagos, 'falhos': falhos, 'sem_pix': sem_pix}
