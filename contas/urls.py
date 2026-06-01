from django.urls import path
from . import views

app_name = 'contas'

urlpatterns = [
    path('login/', views.LoginUsuarioView.as_view(), name='login'),
    path('logout/', views.LogoutUsuarioView.as_view(), name='logout'),
    path('cadastro/', views.CadastroUsuarioView.as_view(), name='cadastro'),
    path('confirmar-email/<uidb64>/<token>/', views.ConfirmarEmailView.as_view(), name='confirmar_email'),
    path('criar-senha/<uidb64>/<token>/', views.CriarSenhaView.as_view(), name='criar_senha'),
]
