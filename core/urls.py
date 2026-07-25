from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.CanilLoginView.as_view(), name="login"),
    path("logout/", views.govbr_logout, name="logout"),
    path("accounts/govbr/login/", views.govbr_login, name="govbr_login"),
    path("accounts/govbr/callback/", views.govbr_callback, name="govbr_callback"),

    path("", views.lista_caes, name="lista_caes"),
    path("caes/novo/", views.cao_form_view, name="cao_novo"),
    path("caes/<int:pk>/", views.ficha_cao, name="ficha_cao"),
    path("caes/<int:pk>/editar/", views.cao_form_view, name="cao_editar"),
    path("caes/<int:pk>/excluir/", views.cao_excluir, name="cao_excluir"),
    path("caes/<int:pk>/ficha-box.pdf", views.cao_ficha_pdf, name="cao_ficha_pdf"),

    path("caes/<int:cao_pk>/vacinas/nova/", views.vacina_form_view, name="vacina_nova"),
    path("caes/<int:cao_pk>/vacinas/<int:pk>/editar/", views.vacina_form_view, name="vacina_editar"),
    path("caes/<int:cao_pk>/medicamentos/novo/", views.medicamento_form_view, name="medicamento_novo"),
    path("caes/<int:cao_pk>/medicamentos/<int:pk>/editar/", views.medicamento_form_view, name="medicamento_editar"),
    path("caes/<int:cao_pk>/pesagens/nova/", views.pesagem_form_view, name="pesagem_nova"),
    path("caes/<int:cao_pk>/pesagens/<int:pk>/editar/", views.pesagem_form_view, name="pesagem_editar"),
    path("caes/<int:cao_pk>/treinamentos/novo/", views.treinamento_form_view, name="treinamento_novo"),
    path("caes/<int:cao_pk>/treinamentos/<int:pk>/editar/", views.treinamento_form_view, name="treinamento_editar"),
    path("caes/<int:cao_pk>/documentos/novo/", views.documento_form_view, name="documento_novo"),

    path("condutores/", views.lista_condutores, name="lista_condutores"),
    path("condutores/novo/", views.condutor_form_view, name="condutor_novo"),
    path("condutores/<int:pk>/editar/", views.condutor_form_view, name="condutor_editar"),
    path("condutores/<int:pk>/excluir/", views.condutor_excluir, name="condutor_excluir"),

    path("relatorios/mensal/", views.relatorio_mensal, name="relatorio_mensal"),
    path("relatorios/mensal/pdf/", views.relatorio_mensal_pdf, name="relatorio_mensal_pdf"),
]
