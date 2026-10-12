from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.CanilLoginView.as_view(), name="login"),
    path("logout/", views.CanilLogoutView.as_view(), name="logout"),
    path("trocar-senha/", views.trocar_senha_obrigatoria, name="trocar_senha_obrigatoria"),

    path("", views.lista_caes, name="lista_caes"),
    path("caes/novo/", views.cao_form_view, name="cao_novo"),
    path("caes/<int:pk>/", views.ficha_cao, name="ficha_cao"),
    path("caes/<int:pk>/editar/", views.cao_form_view, name="cao_editar"),
    path("caes/<int:pk>/excluir/", views.cao_excluir, name="cao_excluir"),
    path("caes/<int:pk>/ficha-box.pdf", views.cao_ficha_pdf, name="cao_ficha_pdf"),
    path("caes/<int:pk>/ficha-sanitaria.pdf", views.cao_ficha_sanitaria_pdf, name="cao_ficha_sanitaria_pdf"),

    path("caes/<int:cao_pk>/vacinas/nova/", views.vacina_form_view, name="vacina_nova"),
    path("caes/<int:cao_pk>/vacinas/<int:pk>/editar/", views.vacina_form_view, name="vacina_editar"),
    path("caes/<int:cao_pk>/vacinas/<int:pk>/excluir/", views.vacina_excluir, name="vacina_excluir"),

    path("caes/<int:cao_pk>/medicamentos/novo/", views.medicamento_form_view, name="medicamento_novo"),
    path("caes/<int:cao_pk>/medicamentos/<int:pk>/editar/", views.medicamento_form_view, name="medicamento_editar"),
    path("caes/<int:cao_pk>/medicamentos/<int:pk>/excluir/", views.medicamento_excluir, name="medicamento_excluir"),

    path("caes/<int:cao_pk>/pesagens/nova/", views.pesagem_form_view, name="pesagem_nova"),
    path("caes/<int:cao_pk>/pesagens/<int:pk>/editar/", views.pesagem_form_view, name="pesagem_editar"),
    path("caes/<int:cao_pk>/pesagens/<int:pk>/excluir/", views.pesagem_excluir, name="pesagem_excluir"),

    path("caes/<int:cao_pk>/treinamentos/novo/", views.treinamento_form_view, name="treinamento_novo"),
    path("caes/<int:cao_pk>/treinamentos/<int:pk>/editar/", views.treinamento_form_view, name="treinamento_editar"),
    path("caes/<int:cao_pk>/treinamentos/<int:pk>/excluir/", views.treinamento_excluir, name="treinamento_excluir"),

    path("caes/<int:cao_pk>/documentos/novo/", views.documento_form_view, name="documento_novo"),
    path("caes/<int:cao_pk>/documentos/<int:pk>/excluir/", views.documento_excluir, name="documento_excluir"),

    path("caes/<int:cao_pk>/vermifugacoes/nova/", views.vermifugacao_form_view, name="vermifugacao_nova"),
    path("caes/<int:cao_pk>/vermifugacoes/<int:pk>/editar/", views.vermifugacao_form_view, name="vermifugacao_editar"),
    path("caes/<int:cao_pk>/vermifugacoes/<int:pk>/excluir/", views.vermifugacao_excluir, name="vermifugacao_excluir"),

    path("caes/<int:cao_pk>/ectoparasitas/novo/", views.ectoparasita_form_view, name="ectoparasita_novo"),
    path("caes/<int:cao_pk>/ectoparasitas/<int:pk>/editar/", views.ectoparasita_form_view, name="ectoparasita_editar"),
    path("caes/<int:cao_pk>/ectoparasitas/<int:pk>/excluir/", views.ectoparasita_excluir, name="ectoparasita_excluir"),

    path("caes/<int:cao_pk>/saude/nova/", views.ocorrencia_saude_form_view, name="ocorrencia_saude_nova"),
    path("caes/<int:cao_pk>/saude/<int:pk>/editar/", views.ocorrencia_saude_form_view, name="ocorrencia_saude_editar"),
    path("caes/<int:cao_pk>/saude/<int:pk>/excluir/", views.ocorrencia_saude_excluir, name="ocorrencia_saude_excluir"),

    path("caes/<int:cao_pk>/visitas/nova/", views.visita_tecnica_form_view, name="visita_tecnica_nova"),
    path("caes/<int:cao_pk>/visitas/<int:pk>/editar/", views.visita_tecnica_form_view, name="visita_tecnica_editar"),
    path("caes/<int:cao_pk>/visitas/<int:pk>/excluir/", views.visita_tecnica_excluir, name="visita_tecnica_excluir"),

    path("condutores/", views.lista_condutores, name="lista_condutores"),
    path("condutores/novo/", views.condutor_form_view, name="condutor_novo"),
    path("condutores/<int:pk>/editar/", views.condutor_form_view, name="condutor_editar"),
    path("condutores/<int:pk>/excluir/", views.condutor_excluir, name="condutor_excluir"),

    path("veterinarios/", views.lista_veterinarios, name="lista_veterinarios"),
    path("veterinarios/novo/", views.veterinario_form_view, name="veterinario_novo"),
    path("veterinarios/<int:pk>/editar/", views.veterinario_form_view, name="veterinario_editar"),
    path("veterinarios/<int:pk>/excluir/", views.veterinario_excluir, name="veterinario_excluir"),

    path("tipos-vacina/", views.lista_tipos_vacina, name="lista_tipos_vacina"),
    path("tipos-vacina/novo/", views.tipo_vacina_form_view, name="tipo_vacina_novo"),
    path("tipos-vacina/<int:pk>/editar/", views.tipo_vacina_form_view, name="tipo_vacina_editar"),
    path("tipos-vacina/<int:pk>/excluir/", views.tipo_vacina_excluir, name="tipo_vacina_excluir"),

    path("relatorios/", views.relatorios_menu, name="relatorios_menu"),
    path("relatorios/mensal/", views.relatorio_mensal, name="relatorio_mensal"),
    path("relatorios/mensal/pdf/", views.relatorio_mensal_pdf, name="relatorio_mensal_pdf"),
    path("relatorios/geral/", views.relatorio_geral, name="relatorio_geral"),
    path("relatorios/geral/pdf/", views.relatorio_geral_pdf, name="relatorio_geral_pdf"),

    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/novo/", views.usuario_form_view, name="usuario_novo"),
    path("usuarios/<int:pk>/editar/", views.usuario_form_view, name="usuario_editar"),
    path("usuarios/<int:pk>/excluir/", views.usuario_excluir, name="usuario_excluir"),
]
