from django.urls import path
from . import views

app_name = 'boloes'

urlpatterns = [
    path('', views.BolaoListView.as_view(), name='bolao_list'),
    path('<int:pk>/', views.BolaoDetailView.as_view(), name='bolao_detail'),
    path('novo/', views.BolaoCreateView.as_view(), name='bolao_create'),
    path('<int:pk>/editar/', views.BolaoUpdateView.as_view(), name='bolao_update'),
    path('<int:pk>/participar/', views.ParticiparBolaoView.as_view(), name='participar'),
    path('meus-jogos/', views.MeusJogosListView.as_view(), name='meus_jogos'),
    path('<int:pk>/resultado/', views.ResultadoBolaoView.as_view(), name='resultado'),
    path('<int:pk>/gerar-ganhadores/', views.GerarGanhadoresView.as_view(), name='gerar_ganhadores'),
]
