from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


STATUS_PAGAMENTO = [
    ('pendente', 'Pendente'),
    ('expirado', 'Expirado'),
    ('confirmado', 'Confirmado'),
    ('cancelado', 'Cancelado'),
]

TIPO_CHAVE_PIX = [
    ('cpf', 'CPF'),
    ('telefone', 'Telefone'),
    ('email', 'E-mail'),
    ('aleatoria', 'Chave aleatória'),
]

AMBIENTE_EFI = [
    ('homologacao', 'Homologação (testes)'),
    ('producao', 'Produção'),
]


class ConfiguracaoPixAdministrador(models.Model):
    """Configuração do Pix do administrador para recebimento de pagamentos."""
    tipo_chave = models.CharField('Tipo de chave', max_length=20, choices=TIPO_CHAVE_PIX)
    chave_pix = models.CharField('Chave Pix', max_length=150)
    nome_recebedor = models.CharField('Nome do recebedor', max_length=100)
    banco = models.CharField('Banco', max_length=100)
    documento_recebedor = models.CharField('Documento (CPF/CNPJ)', max_length=20)
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    # Credenciais EFI Bank para confirmação automática de PIX
    client_id_efi = models.CharField('Client ID (EFI Bank)', max_length=200, blank=True,
                                     help_text='Client ID da aplicação EFI Bank (ex-Gerencianet)')
    client_secret_efi = models.CharField('Client Secret (EFI Bank)', max_length=200, blank=True,
                                         help_text='Client Secret da aplicação EFI Bank')
    certificado_efi = models.FileField('Certificado EFI (.p12/.pem)', upload_to='certificados/', blank=True, null=True,
                                       help_text='Arquivo de certificado mTLS (.p12 ou .pem) gerado no portal EFI Bank')
    ambiente_efi = models.CharField('Ambiente EFI', max_length=20, choices=AMBIENTE_EFI, default='homologacao',
                                    help_text='Use Homologação para testes e Produção para cobranças reais')

    class Meta:
        verbose_name = 'Configuração Pix do Administrador'
        verbose_name_plural = 'Configurações Pix do Administrador'

    def __str__(self):
        return f'{self.nome_recebedor} — {self.chave_pix}'


class ConfiguracaoEmail(models.Model):
    """Configuração de e-mail SMTP do sistema."""
    servidor_smtp = models.CharField('Servidor SMTP', max_length=200)
    porta = models.PositiveIntegerField('Porta', default=587)
    usuario_email = models.EmailField('Usuário de e-mail')
    senha_email = models.CharField('Senha do e-mail', max_length=200)
    usar_tls = models.BooleanField('Usar TLS', default=True)
    email_remetente = models.EmailField('E-mail remetente')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Configuração de E-mail'
        verbose_name_plural = 'Configurações de E-mail'

    def __str__(self):
        return f'{self.email_remetente} ({self.servidor_smtp})'


class Pagamento(models.Model):
    """Registro de pagamento Pix de uma participação no bolão."""
    from boloes.models import ParticipacaoBolao

    participacao = models.OneToOneField(
        'boloes.ParticipacaoBolao',
        on_delete=models.PROTECT,
        related_name='pagamento',
        verbose_name='Participação',
    )
    lote = models.ForeignKey(
        'PagamentoLote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagamentos',
        verbose_name='Lote de pagamento',
    )
    valor = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_PAGAMENTO, default='pendente')
    txid = models.CharField('ID da transação', max_length=100, blank=True)
    qr_code = models.TextField('QR Code (base64)', blank=True)
    pix_copia_cola = models.TextField('Pix copia e cola', blank=True)
    data_criacao = models.DateTimeField('Criado em', auto_now_add=True)
    data_expiracao = models.DateTimeField('Expira em', null=True, blank=True)
    data_confirmacao = models.DateTimeField('Confirmado em', null=True, blank=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagamentos_confirmados',
        verbose_name='Confirmado por',
    )

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Pagamento {self.pk} — {self.get_status_display()}'

    @property
    def esta_expirado(self):
        if self.data_expiracao and self.status == 'pendente':
            return timezone.now() > self.data_expiracao
        return False


class PagamentoLote(models.Model):
    """
    Pagamento único (um só PIX) que quita várias participações de uma vez.
    O usuário seleciona os bolões que quer pagar, o sistema gera um QR Code
    com o valor total, e ao confirmar o pagamento todas as participações são quitadas.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='lotes_pagamento',
        verbose_name='Usuário',
    )
    valor_total = models.DecimalField('Valor total (R$)', max_digits=10, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_PAGAMENTO, default='pendente')
    txid = models.CharField('ID da transação (lote)', max_length=100, blank=True, unique=True)
    qr_code = models.TextField('QR Code (base64)', blank=True)
    pix_copia_cola = models.TextField('Pix copia e cola', blank=True)
    data_criacao = models.DateTimeField('Criado em', auto_now_add=True)
    data_expiracao = models.DateTimeField('Expira em', null=True, blank=True)
    data_confirmacao = models.DateTimeField('Confirmado em', null=True, blank=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lotes_confirmados',
        verbose_name='Confirmado por',
    )

    class Meta:
        verbose_name = 'Pagamento em lote'
        verbose_name_plural = 'Pagamentos em lote'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Lote {self.pk} — {self.usuario} — R${self.valor_total} — {self.get_status_display()}'

    @property
    def esta_expirado(self):
        if self.data_expiracao and self.status == 'pendente':
            return timezone.now() > self.data_expiracao
        return False

