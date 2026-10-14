from django.urls import path
from . import views

urlpatterns = [
    path("", views.painel, name="gestao_painel"),
    path("unidades/", views.lista_unidades, name="gestao_unidades"),
    path("unidades/nova/", views.unidade_form_view, name="gestao_unidade_nova"),
    path("unidades/<int:pk>/editar/", views.unidade_form_view, name="gestao_unidade_editar"),
    path("unidades/<int:pk>/excluir/", views.unidade_excluir, name="gestao_unidade_excluir"),
    path("canis/novo/", views.canil_form_view, name="gestao_canil_novo"),
    path("canis/<int:pk>/editar/", views.canil_form_view, name="gestao_canil_editar"),
    path("canis/<int:pk>/excluir/", views.canil_excluir, name="gestao_canil_excluir"),
    path("canis/<int:pk>/acessar/", views.acessar_canil, name="gestao_canil_acessar"),
    path("sair-canil/", views.sair_canil, name="gestao_sair_canil"),
    path("usuarios/", views.lista_usuarios_canis, name="gestao_usuarios"),
    path("usuarios/novo/", views.usuario_form_view, name="gestao_usuario_novo"),
    path("usuarios/<int:pk>/editar/", views.usuario_form_view, name="gestao_usuario_editar"),
    path("usuarios/<int:pk>/excluir/", views.usuario_excluir, name="gestao_usuario_excluir"),
    path("usuarios/<int:pk>/senha/", views.usuario_resetar_senha, name="gestao_usuario_senha"),
    path("manutencao/atualizar-banco/", views.atualizar_banco, name="gestao_atualizar_banco"),
]
