from django.contrib import admin
from .models import PixUsuario

@admin.register(PixUsuario)
class PixUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_chave', 'chave_pix', 'banco', 'ativo')
    list_filter = ('tipo_chave', 'ativo')
    search_fields = ('usuario__nome_completo', 'chave_pix')
