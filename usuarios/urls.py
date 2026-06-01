from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('perfil/', views.PerfilUsuarioView.as_view(), name='perfil'),
    path('pix/', views.PixUsuarioUpdateView.as_view(), name='pix'),
]
