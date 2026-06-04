"""
Integração com Mercado Pago para cobranças via PIX.
Documentação: https://www.mercadopago.com.br/developers/pt/docs/checkout-api/payment-methods/other-payment-methods/brasil/pix
"""
from datetime import datetime, timedelta

import mercadopago


def tem_credenciais_mp(config_pix) -> bool:
    """Retorna True se o Access Token do Mercado Pago estiver configurado."""
    return bool(config_pix.mp_access_token)


def _get_sdk(config_pix):
    return mercadopago.SDK(config_pix.mp_access_token)


def criar_cobranca_mp(config_pix, valor: float, email_pagador: str, external_reference: str) -> dict:
    """
    Cria uma cobrança PIX no Mercado Pago.

    Parâmetros:
        config_pix: ConfiguracaoPixAdministrador com mp_access_token preenchido
        valor: valor em float (ex: 25.50)
        email_pagador: e-mail do pagador (obrigatório pelo MP)
        external_reference: identificador único da transação (txid sem hífens, max 35 chars)

    Retorna dict com:
        'mp_payment_id'  — ID numérico do pagamento no MP (string) — usado como txid no BD
        'pix_copia_cola' — texto copia-e-cola (qr_code da API)
        'qr_code_base64' — imagem PNG base64 pronta para <img> (sem prefixo data:)
    """
    sdk = _get_sdk(config_pix)

    expiracao = datetime.now() + timedelta(minutes=30)
    # MP exige offset de fuso no formato: 2025-01-01T00:00:00.000-03:00
    expiracao_str = expiracao.strftime('%Y-%m-%dT%H:%M:%S.000-03:00')

    payment_data = {
        'transaction_amount': round(float(valor), 2),
        'description': 'Bolão Copa do Mundo',
        'payment_method_id': 'pix',
        'payer': {
            'email': email_pagador,
        },
        'external_reference': external_reference,
        'date_of_expiration': expiracao_str,
    }

    result = sdk.payment().create(payment_data)

    if result['status'] not in (200, 201):
        raise Exception(
            f'Erro Mercado Pago ao criar cobrança (HTTP {result["status"]}): {result["response"]}'
        )

    response = result['response']
    txd = response.get('point_of_interaction', {}).get('transaction_data', {})

    return {
        'mp_payment_id': str(response['id']),
        'pix_copia_cola': txd.get('qr_code', ''),
        'qr_code_base64': txd.get('qr_code_base64', ''),
    }


def verificar_pagamento_mp(config_pix, mp_payment_id: str) -> dict:
    """
    Consulta o status de um pagamento no Mercado Pago pelo ID numérico.
    Retorna o dict de resposta da API (campo 'status' = 'approved' quando pago).
    """
    sdk = _get_sdk(config_pix)
    result = sdk.payment().get(int(mp_payment_id))
    if result['status'] != 200:
        raise Exception(
            f'Erro Mercado Pago ao consultar pagamento {mp_payment_id}: {result["response"]}'
        )
    return result['response']
