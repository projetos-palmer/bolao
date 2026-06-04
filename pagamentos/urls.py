from django.urls import path
from . import views

app_name = 'pagamentos'

urlpatterns = [
    path('<int:participacao_pk>/pix/', views.PagamentoPixDetailView.as_view(), name='pagamento_pix'),
    path('<int:pk>/confirmar/', views.ConfirmarPagamentoView.as_view(), name='confirmar_pagamento'),
    path('<int:pk>/confirmado/', views.PagamentoConfirmadoView.as_view(), name='pagamento_confirmado'),
    # Polling de status (chamado pelo JavaScript da página de pagamento)
    path('<int:pk>/status/', views.StatusPagamentoView.as_view(), name='status_pagamento'),
    # Webhook EFI Bank — recebe notificações automáticas de PIX recebido
    path('webhook/pix/', views.WebhookPixEfiView.as_view(), name='webhook_pix_efi'),
    # Webhook Mercado Pago — recebe notificações de PIX aprovado
    path('webhook/mp/', views.WebhookPixMPView.as_view(), name='webhook_pix_mp'),
    # Ação admin: registrar webhook no EFI Bank
    path('webhook/registrar/', views.RegistrarWebhookEfiView.as_view(), name='registrar_webhook_efi'),
    # Pagamento em lote (múltiplos bolões, um único PIX)
    path('lote/novo/', views.PagamentoLoteCreateView.as_view(), name='criar_lote'),
    path('lote/<int:pk>/', views.PagamentoLoteDetailView.as_view(), name='pagamento_lote'),
    path('lote/<int:pk>/status/', views.StatusPagamentoLoteView.as_view(), name='status_lote'),
    path('lote/<int:pk>/confirmado/', views.PagamentoLoteConfirmadoView.as_view(), name='lote_confirmado'),
]
