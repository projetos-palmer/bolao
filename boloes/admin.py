from django.contrib import admin
from .models import Bolao, ParticipacaoBolao, Premio

@admin.register(Bolao)
class BolaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'jogo', 'status', 'valor_participacao', 'percentual_premiacao')
    list_filter = ('status',)

@admin.register(ParticipacaoBolao)
class ParticipacaoBolaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'bolao', 'placar_mandante', 'placar_visitante', 'status')
    list_filter = ('status',)
    search_fields = ('usuario__nome_completo', 'bolao__nome')

@admin.register(Premio)
class PremioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'bolao', 'valor', 'status_pagamento')
    list_filter = ('status_pagamento',)
