from django.contrib import admin
from .models import Selecao, Jogo, VotoCampeao

@admin.register(Selecao)
class SelecaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'icone')
    search_fields = ('nome', 'sigla')

@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'data_hora', 'fase', 'status')
    list_filter = ('status', 'fase')
    search_fields = ('selecao_mandante__nome', 'selecao_visitante__nome')


@admin.register(VotoCampeao)
class VotoCampeaoAdmin(admin.ModelAdmin):
    list_display = ('selecao', 'ip', 'atualizado_em')
    list_filter = ('selecao', 'criado_em', 'atualizado_em')
    search_fields = ('selecao__nome', 'session_key', 'ip')
    readonly_fields = ('criado_em', 'atualizado_em')
