from django.urls import path
from . import views

urlpatterns = [
    path("", views.estoque, name="racoes_estoque"),
    path("nova/", views.racao_form_view, name="racao_nova"),
    path("<int:pk>/editar/", views.racao_form_view, name="racao_editar"),
    path("<int:pk>/excluir/", views.racao_excluir, name="racao_excluir"),
    path("<int:pk>/extrato/", views.extrato, name="racao_extrato"),
    path("entradas/nova/", views.entrada_nova, name="racao_entrada_nova"),
    path("saidas/nova/", views.saida_nova, name="racao_saida_nova"),
]
