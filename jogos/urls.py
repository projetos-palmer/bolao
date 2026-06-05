from django.urls import path
from . import views

app_name = 'jogos'

urlpatterns = [
    path('', views.PaginaInicialView.as_view(), name='inicio'),
    path('votar-campeao/', views.votar_campeao, name='votar_campeao'),
    path('lista/', views.JogoListView.as_view(), name='jogo_list'),
    path('<int:pk>/', views.JogoDetailView.as_view(), name='jogo_detail'),
    path('novo/', views.JogoCreateView.as_view(), name='jogo_create'),
    path('<int:pk>/editar/', views.JogoUpdateView.as_view(), name='jogo_update'),
    path('<int:pk>/excluir/', views.JogoDeleteView.as_view(), name='jogo_delete'),
    path('<int:pk>/data-hora.json', views.jogo_data_hora_json, name='jogo_data_hora_json'),
]
