from django.db import models
from django.conf import settings


TIPO_CHAVE_PIX = [
    ('cpf', 'CPF'),
    ('telefone', 'Telefone'),
    ('email', 'E-mail'),
    ('aleatoria', 'Chave aleatória'),
]


class PixUsuario(models.Model):
    """Dados Pix do usuário para recebimento de prêmios."""
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pix',
        verbose_name='Usuário',
    )
    tipo_chave = models.CharField('Tipo de chave', max_length=20, choices=TIPO_CHAVE_PIX)
    chave_pix = models.CharField('Chave Pix', max_length=150)
    nome_recebedor = models.CharField('Nome do recebedor', max_length=100)
    banco = models.CharField('Banco', max_length=100)
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Pix do usuário'
        verbose_name_plural = 'Pix dos usuários'

    def __str__(self):
        return f'{self.usuario.nome_completo} — {self.get_tipo_chave_display()}'
