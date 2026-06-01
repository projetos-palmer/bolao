from django.contrib import admin
from .models import ConfiguracaoPixAdministrador, ConfiguracaoEmail, Pagamento

@admin.register(ConfiguracaoPixAdministrador)
class ConfiguracaoPixAdmin(admin.ModelAdmin):
    list_display = ('tipo_chave', 'chave_pix', 'nome_recebedor', 'banco', 'ativo')

@admin.register(ConfiguracaoEmail)
class ConfiguracaoEmailAdmin(admin.ModelAdmin):
    list_display = ('servidor_smtp', 'porta', 'usuario_email')

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('participacao', 'valor', 'status', 'data_criacao', 'data_confirmacao')
    list_filter = ('status',)
