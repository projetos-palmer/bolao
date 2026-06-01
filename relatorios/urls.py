from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    path('bolao/<int:pk>/pdf/', views.RelatorioBolaoPDFView.as_view(), name='bolao_pdf'),
]
