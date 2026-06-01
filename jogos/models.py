from django.db import models
from django.utils import timezone
from datetime import timedelta


FASE_CHOICES = [
    ('grupos', 'Fase de Grupos'),
    ('oitavas', 'Oitavas de Final'),
    ('quartas', 'Quartas de Final'),
    ('semi', 'Semifinal'),
    ('terceiro', 'Disputa 3º lugar'),
    ('final', 'Final'),
]

STATUS_JOGO = [
    ('agendado', 'Agendada'),
    ('aberto', 'Aberta para bolão'),
    ('bloqueado', 'Bloqueada para apostas'),
    ('andamento', 'Em andamento'),
    ('encerrado', 'Encerrada'),
    ('resultado', 'Resultado informado'),
    ('premiacao', 'Premiação gerada'),
    ('pago', 'Pagamentos realizados'),
]


class Selecao(models.Model):
    """Seleção participante da Copa."""
    nome = models.CharField('Nome', max_length=100)
    sigla = models.CharField('Sigla', max_length=5)
    bandeira = models.ImageField('Bandeira', upload_to='bandeiras/', blank=True, null=True)
    icone = models.CharField('Ícone (emoji)', max_length=10, blank=True)

    class Meta:
        verbose_name = 'Seleção'
        verbose_name_plural = 'Seleções'
        ordering = ['nome']

    def __str__(self):
        return f'{self.icone} {self.nome}' if self.icone else self.nome


class Jogo(models.Model):
    """Partida da Copa do Mundo."""
    selecao_mandante = models.ForeignKey(
        Selecao,
        on_delete=models.PROTECT,
        related_name='jogos_mandante',
        verbose_name='Seleção mandante',
    )
    selecao_visitante = models.ForeignKey(
        Selecao,
        on_delete=models.PROTECT,
        related_name='jogos_visitante',
        verbose_name='Seleção visitante',
    )
    data_hora = models.DateTimeField('Data e hora da partida')
    estadio = models.CharField('Estádio', max_length=150, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    fase = models.CharField('Fase', max_length=20, choices=FASE_CHOICES, default='grupos')
    status = models.CharField('Status', max_length=20, choices=STATUS_JOGO, default='agendado')
    placar_mandante = models.PositiveSmallIntegerField('Placar mandante', null=True, blank=True)
    placar_visitante = models.PositiveSmallIntegerField('Placar visitante', null=True, blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Jogo'
        verbose_name_plural = 'Jogos'
        ordering = ['data_hora']

    def __str__(self):
        return f'{self.selecao_mandante} x {self.selecao_visitante} — {self.data_hora.strftime("%d/%m/%Y %H:%M")}'

    @property
    def limite_aposta(self):
        """Retorna o horário limite para apostas (5 min antes do jogo)."""
        return self.data_hora - timedelta(minutes=5)

    @property
    def esta_aberto_para_apostas(self):
        return timezone.now() < self.limite_aposta and self.status in ('aberto',)

    @property
    def resultado_definido(self):
        return self.placar_mandante is not None and self.placar_visitante is not None
