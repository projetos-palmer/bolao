import uuid
from django.db import models
from django.conf import settings
from jogos.models import Jogo


STATUS_BOLAO = [
    ('rascunho', 'Rascunho'),
    ('aberto', 'Aberto'),
    ('fechado', 'Fechado'),
    ('encerrado', 'Encerrado'),
    ('premiacao', 'Premiação gerada'),
    ('pago', 'Pagamentos realizados'),
]

STATUS_PARTICIPACAO = [
    ('aguardando', 'Aguardando pagamento'),
    ('expirado', 'Pagamento expirado'),
    ('confirmado', 'Pagamento confirmado'),
    ('valido', 'Palpite válido'),
    ('vencedor', 'Palpite vencedor'),
    ('nao_premiado', 'Palpite não premiado'),
    ('premio_pago', 'Pagamento do prêmio realizado'),
]

REGRA_SEM_GANHADOR = [
    ('acumular', 'Acumular para próximo bolão'),
    ('devolver', 'Devolver aos participantes'),
    ('reter', 'Manter valor retido'),
]


class Bolao(models.Model):
    """Bolão vinculado a um jogo da Copa."""
    jogo = models.ForeignKey(Jogo, on_delete=models.PROTECT, related_name='boloes', verbose_name='Jogo')
    nome = models.CharField('Nome do bolão', max_length=150)
    valor_participacao = models.DecimalField('Valor de participação (R$)', max_digits=10, decimal_places=2)
    percentual_premiacao = models.PositiveSmallIntegerField(
        'Percentual de premiação (%)',
        default=70,
        help_text='De 0 a 100%',
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_BOLAO, default='rascunho')
    data_abertura = models.DateTimeField('Data de abertura', null=True, blank=True)
    data_fechamento = models.DateTimeField('Data de fechamento', null=True, blank=True)
    regra_sem_ganhador = models.CharField(
        'Regra sem ganhador',
        max_length=20,
        choices=REGRA_SEM_GANHADOR,
        default='acumular',
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Bolão'
        verbose_name_plural = 'Bolões'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome

    @property
    def valor_total_arrecadado(self):
        return self.participacoes.filter(
            status__in=['confirmado', 'valido', 'vencedor', 'nao_premiado', 'premio_pago']
        ).count() * self.valor_participacao

    @property
    def participacoes_pagas(self):
        return self.participacoes.filter(
            status__in=['confirmado', 'valido', 'vencedor', 'nao_premiado', 'premio_pago']
        ).count()

    @property
    def valor_total_premio(self):
        return (self.valor_total_arrecadado * self.percentual_premiacao) / 100


class ParticipacaoBolao(models.Model):
    """Palpite e participação de um usuário em um bolão."""
    codigo_identificador = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='participacoes',
        verbose_name='Usuário',
    )
    bolao = models.ForeignKey(
        Bolao,
        on_delete=models.PROTECT,
        related_name='participacoes',
        verbose_name='Bolão',
    )
    placar_mandante = models.PositiveSmallIntegerField('Placar mandante')
    placar_visitante = models.PositiveSmallIntegerField('Placar visitante')
    data_palpite = models.DateTimeField('Data do palpite', auto_now_add=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_PARTICIPACAO, default='aguardando')
    bloqueado_para_edicao = models.BooleanField('Bloqueado para edição', default=True)

    class Meta:
        verbose_name = 'Participação'
        verbose_name_plural = 'Participações'
        ordering = ['-data_palpite']

    def __str__(self):
        return f'{self.usuario} — {self.bolao} ({self.placar_mandante}x{self.placar_visitante})'

    @property
    def acertou_placar(self):
        jogo = self.bolao.jogo
        return (
            jogo.placar_mandante is not None
            and jogo.placar_visitante is not None
            and self.placar_mandante == jogo.placar_mandante
            and self.placar_visitante == jogo.placar_visitante
        )


class Premio(models.Model):
    """Registro de prêmio a pagar ao ganhador."""
    bolao = models.ForeignKey(Bolao, on_delete=models.PROTECT, related_name='premios', verbose_name='Bolão')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='premios',
        verbose_name='Usuário',
    )
    participacao = models.ForeignKey(
        ParticipacaoBolao,
        on_delete=models.PROTECT,
        related_name='premios',
        verbose_name='Participação',
    )
    valor = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    status_pagamento = models.CharField(
        'Status do pagamento',
        max_length=20,
        choices=[('pendente', 'Pendente'), ('pago', 'Pago'), ('falhou', 'Falhou')],
        default='pendente',
    )
    data_pagamento = models.DateTimeField('Data do pagamento', null=True, blank=True)
    comprovante = models.TextField('Comprovante', blank=True)

    class Meta:
        verbose_name = 'Prêmio'
        verbose_name_plural = 'Prêmios'

    def __str__(self):
        return f'Prêmio R${self.valor} — {self.usuario}'
