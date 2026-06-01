from django.contrib import admin
from .models import Selecao, Jogo

@admin.register(Selecao)
class SelecaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'icone')
    search_fields = ('nome', 'sigla')

@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'data_hora', 'fase', 'status')
    list_filter = ('status', 'fase')
    search_fields = ('selecao_mandante__nome', 'selecao_visitante__nome')
