from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['cpf', 'nome_completo', 'email', 'email_confirmado', 'is_active']
    list_filter = ['is_active', 'email_confirmado', 'is_staff']
    search_fields = ['email', 'nome_completo', 'cpf']
    ordering = ['nome_completo']
    fieldsets = (
        (None, {'fields': ('cpf', 'password')}),
        ('Dados pessoais', {'fields': ('nome_completo', 'email', 'telefone')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'email_confirmado', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cpf', 'email', 'nome_completo', 'telefone', 'password1', 'password2'),
        }),
    )
