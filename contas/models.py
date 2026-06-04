from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):

    def create_user(self, cpf, email, nome_completo, telefone, password=None):
        if not cpf:
            raise ValueError('O CPF é obrigatório.')
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        email = self.normalize_email(email)
        usuario = self.model(
            cpf=cpf,
            email=email,
            nome_completo=nome_completo,
            telefone=telefone,
        )
        if password:
            usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, cpf, email, nome_completo, telefone, password=None):
        usuario = self.create_user(cpf, email, nome_completo, telefone, password)
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.is_active = True
        usuario.email_confirmado = True
        usuario.save(using=self._db)
        return usuario

class Usuario(AbstractBaseUser, PermissionsMixin):
    cpf = models.CharField('CPF', max_length=14, unique=True)
    nome_completo = models.CharField('Nome completo', max_length=150)
    telefone = models.CharField('Telefone', max_length=15, unique=True)
    email = models.EmailField('E-mail', unique=True)
    email_confirmado = models.BooleanField('E-mail confirmado', default=False)
    data_cadastro = models.DateTimeField('Data de cadastro', auto_now_add=True)
    is_active = models.BooleanField('Ativo', default=False)
    is_staff = models.BooleanField('Staff', default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['email', 'nome_completo', 'telefone']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome_completo']

    def __str__(self):
        return self.nome_completo

    @property
    def primeiro_nome(self):
        return self.nome_completo.split()[0]
