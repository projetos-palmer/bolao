from django.urls import path
from . import views

app_name = 'painel'

urlpatterns = [
    path('dashboard/', views.DashboardAdministradorView.as_view(), name='dashboard'),
    path('pix/', views.ConfiguracaoPixUpdateView.as_view(), name='configuracao_pix'),
    path('email/', views.ConfiguracaoEmailUpdateView.as_view(), name='configuracao_email'),
    path('bolao/<int:pk>/pagar-premios/', views.PagarPremiosBolaoView.as_view(), name='pagar_premios_bolao'),
]
