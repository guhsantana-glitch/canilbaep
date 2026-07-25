from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Q

from .models import (
    Cao, Condutor, Vacina, Medicamento, Pesagem, Treinamento, Documento,
    Veterinario, TipoVacina,
)
from .forms import (
    CaoForm, CondutorForm, VacinaForm, MedicamentoForm,
    PesagemForm, TreinamentoForm, DocumentoForm, RelatorioMensalForm, RelatorioGeralForm,
    VeterinarioForm, TipoVacinaForm,
)
from .pdf_utils import gerar_ficha_box, gerar_relatorio_mensal, gerar_relatorio_geral_mensal


class CanilLoginView(LoginView):
    template_name = "core/login.html"


class CanilLogoutView(LogoutView):
    next_page = "login"


def eh_superusuario(user):
    return user.is_superuser


# ---------- Cães ----------

@login_required
def lista_caes(request):
    caes = Cao.objects.select_related("condutor_atual").all()
    status = request.GET.get("status")
    busca = request.GET.get("q")
    if status:
        caes = caes.filter(status=status)
    if busca:
        caes = caes.filter(nome__icontains=busca)
    return render(request, "core/lista_caes.html", {
        "caes": caes, "status_choices": Cao.Status.choices,
        "status_selecionado": status, "busca": busca or "",
    })


@login_required
def ficha_cao(request, pk):
    cao = get_object_or_404(Cao, pk=pk)
    treinamentos = cao.treinamentos.all()
    evolucao = [
        {"data": t.data.strftime("%d/%m/%Y"), "nota": float(t.nota_avaliacao)}
        for t in treinamentos.exclude(nota_avaliacao__isnull=True).order_by("data")
    ]
    return render(request, "core/ficha_cao.html", {
        "cao": cao,
        "pesagens": cao.pesagens.all()[:30],
        "vacinas": cao.vacinas.select_related("tipo", "veterinario").all(),
        "medicamentos": cao.medicamentos.select_related("veterinario").all(),
        "treinamentos": treinamentos,
        "documentos": cao.documentos.all(),
        "evolucao_json": evolucao,
    })


@login_required
def cao_form_view(request, pk=None):
    cao = get_object_or_404(Cao, pk=pk) if pk else None
    if request.method == "POST":
        form = CaoForm(request.POST, request.FILES, instance=cao)
        if form.is_valid():
            cao = form.save()
            messages.success(request, f"Cão '{cao.nome}' salvo com sucesso.")
            return redirect("ficha_cao", pk=cao.pk)
    else:
        form = CaoForm(instance=cao)
    return render(request, "core/cao_form.html", {"form": form, "cao": cao})


@login_required
def cao_excluir(request, pk):
    cao = get_object_or_404(Cao, pk=pk)
    if request.method == "POST":
        nome = cao.nome
        cao.delete()
        messages.success(request, f"Cão '{nome}' excluído.")
        return redirect("lista_caes")
    return render(request, "core/confirmar_exclusao.html", {"objeto": cao, "tipo": "cão"})


@login_required
def cao_ficha_pdf(request, pk):
    cao = get_object_or_404(Cao, pk=pk)
    buffer = gerar_ficha_box(cao)
    resp = HttpResponse(buffer, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="ficha_box_{cao.nome}.pdf"'
    return resp


# ---------- Registros vinculados ao cão (vacina, medicamento, pesagem, treinamento, documento) ----------

def _registro_form_view(request, pk, cao_pk, Model, FormClass, template, campo_cao="cao"):
    cao = get_object_or_404(Cao, pk=cao_pk)
    instancia = get_object_or_404(Model, pk=pk) if pk else None
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=instancia)
        if form.is_valid():
            obj = form.save(commit=False)
            setattr(obj, campo_cao, cao)
            obj.save()
            messages.success(request, "Registro salvo com sucesso.")
            return redirect("ficha_cao", pk=cao.pk)
    else:
        form = FormClass(instance=instancia)
    return render(request, template, {"form": form, "cao": cao})


def _registro_excluir_view(request, cao_pk, pk, Model):
    cao = get_object_or_404(Cao, pk=cao_pk)
    obj = get_object_or_404(Model, pk=pk, cao=cao)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Registro excluído.")
        return redirect("ficha_cao", pk=cao.pk)
    return render(request, "core/confirmar_exclusao.html", {"objeto": obj, "tipo": "registro"})


@login_required
def vacina_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Vacina, VacinaForm, "core/registro_form.html")


@login_required
def vacina_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Vacina)


@login_required
def medicamento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Medicamento, MedicamentoForm, "core/registro_form.html")


@login_required
def medicamento_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Medicamento)


@login_required
def pesagem_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Pesagem, PesagemForm, "core/registro_form.html")


@login_required
def pesagem_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Pesagem)


@login_required
def treinamento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Treinamento, TreinamentoForm, "core/registro_form.html")


@login_required
def treinamento_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Treinamento)


@login_required
def documento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Documento, DocumentoForm, "core/registro_form.html")


@login_required
def documento_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Documento)


# ---------- Condutores ----------

@login_required
def lista_condutores(request):
    condutores = Condutor.objects.all()
    return render(request, "core/lista_condutores.html", {"condutores": condutores})


@login_required
def condutor_form_view(request, pk=None):
    condutor = get_object_or_404(Condutor, pk=pk) if pk else None
    if request.method == "POST":
        form = CondutorForm(request.POST, instance=condutor)
        if form.is_valid():
            form.save()
            messages.success(request, "Condutor salvo com sucesso.")
            return redirect("lista_condutores")
    else:
        form = CondutorForm(instance=condutor)
    return render(request, "core/condutor_form.html", {"form": form, "condutor": condutor})


@login_required
def condutor_excluir(request, pk):
    condutor = get_object_or_404(Condutor, pk=pk)
    if request.method == "POST":
        condutor.delete()
        messages.success(request, "Condutor excluído.")
        return redirect("lista_condutores")
    return render(request, "core/confirmar_exclusao.html", {"objeto": condutor, "tipo": "condutor"})


# ---------- Veterinários ----------

@login_required
def lista_veterinarios(request):
    veterinarios = Veterinario.objects.all()
    return render(request, "core/lista_veterinarios.html", {"veterinarios": veterinarios})


@login_required
def veterinario_form_view(request, pk=None):
    veterinario = get_object_or_404(Veterinario, pk=pk) if pk else None
    if request.method == "POST":
        form = VeterinarioForm(request.POST, instance=veterinario)
        if form.is_valid():
            form.save()
            messages.success(request, "Veterinário salvo com sucesso.")
            return redirect("lista_veterinarios")
    else:
        form = VeterinarioForm(instance=veterinario)
    return render(request, "core/veterinario_form.html", {"form": form, "veterinario": veterinario})


@login_required
def veterinario_excluir(request, pk):
    veterinario = get_object_or_404(Veterinario, pk=pk)
    if request.method == "POST":
        veterinario.delete()
        messages.success(request, "Veterinário excluído.")
        return redirect("lista_veterinarios")
    return render(request, "core/confirmar_exclusao.html", {"objeto": veterinario, "tipo": "veterinário"})


# ---------- Tipos de vacina (catálogo) ----------

@login_required
def lista_tipos_vacina(request):
    tipos = TipoVacina.objects.all()
    return render(request, "core/lista_tipos_vacina.html", {"tipos": tipos})


@login_required
def tipo_vacina_form_view(request, pk=None):
    tipo = get_object_or_404(TipoVacina, pk=pk) if pk else None
    if request.method == "POST":
        form = TipoVacinaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de vacina salvo com sucesso.")
            return redirect("lista_tipos_vacina")
    else:
        form = TipoVacinaForm(instance=tipo)
    return render(request, "core/tipo_vacina_form.html", {"form": form, "tipo": tipo})


@login_required
def tipo_vacina_excluir(request, pk):
    tipo = get_object_or_404(TipoVacina, pk=pk)
    if request.method == "POST":
        tipo.delete()
        messages.success(request, "Tipo de vacina excluído.")
        return redirect("lista_tipos_vacina")
    return render(request, "core/confirmar_exclusao.html", {"objeto": tipo, "tipo": "tipo de vacina"})


# ---------- Relatórios ----------

@login_required
def relatorios_menu(request):
    return render(request, "core/relatorios_menu.html")


@login_required
def relatorio_mensal(request):
    resultado = None
    if request.method == "POST":
        form = RelatorioMensalForm(request.POST)
        if form.is_valid():
            cao = form.cleaned_data["cao"]
            di = form.cleaned_data["data_inicio"]
            df = form.cleaned_data["data_fim"]
            resultado = {
                "cao": cao, "data_inicio": di, "data_fim": df,
                "pesagens": cao.pesagens.filter(data__range=(di, df)),
                "vacinas": cao.vacinas.filter(data_aplicacao__range=(di, df)),
                "medicamentos": cao.medicamentos.filter(data_inicio__range=(di, df)),
            }
    else:
        form = RelatorioMensalForm()
    return render(request, "core/relatorio_mensal.html", {"form": form, "resultado": resultado})


@login_required
def relatorio_mensal_pdf(request):
    form = RelatorioMensalForm(request.GET)
    if not form.is_valid():
        return redirect("relatorio_mensal")
    cao = form.cleaned_data["cao"]
    di = form.cleaned_data["data_inicio"]
    df = form.cleaned_data["data_fim"]
    buffer = gerar_relatorio_mensal(
        cao, di, df,
        pesagens=cao.pesagens.filter(data__range=(di, df)),
        vacinas=cao.vacinas.filter(data_aplicacao__range=(di, df)),
        medicamentos=cao.medicamentos.filter(data_inicio__range=(di, df)),
    )
    resp = HttpResponse(buffer, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="relatorio_{cao.nome}_{di}_{df}.pdf"'
    return resp


def _montar_linhas_relatorio_geral(di, df, apenas_ativos):
    caes = Cao.objects.select_related("condutor_atual").all()
    if apenas_ativos:
        caes = caes.filter(status=Cao.Status.ATIVO)
    linhas = []
    for cao in caes.order_by("nome"):
        linhas.append({
            "nome": cao.nome,
            "box": cao.box,
            "condutor": cao.condutor_atual.nome if cao.condutor_atual else None,
            "status": cao.get_status_display(),
            "peso_atual": cao.peso_atual(),
            "qtd_vacinas": cao.vacinas.filter(data_aplicacao__range=(di, df)).count(),
            "qtd_medicamentos": cao.medicamentos.filter(data_inicio__range=(di, df)).count(),
            "qtd_treinamentos": cao.treinamentos.filter(data__range=(di, df)).count(),
        })
    return linhas


@login_required
def relatorio_geral(request):
    resultado = None
    if request.method == "POST":
        form = RelatorioGeralForm(request.POST)
        if form.is_valid():
            di = form.cleaned_data["data_inicio"]
            df = form.cleaned_data["data_fim"]
            apenas_ativos = form.cleaned_data["apenas_ativos"]
            resultado = {
                "data_inicio": di, "data_fim": df, "apenas_ativos": apenas_ativos,
                "linhas": _montar_linhas_relatorio_geral(di, df, apenas_ativos),
            }
    else:
        form = RelatorioGeralForm(initial={"apenas_ativos": True})
    return render(request, "core/relatorio_geral.html", {"form": form, "resultado": resultado})


@login_required
def relatorio_geral_pdf(request):
    form = RelatorioGeralForm(request.GET)
    if not form.is_valid():
        return redirect("relatorio_geral")
    di = form.cleaned_data["data_inicio"]
    df = form.cleaned_data["data_fim"]
    apenas_ativos = form.cleaned_data["apenas_ativos"]
    linhas = _montar_linhas_relatorio_geral(di, df, apenas_ativos)
    buffer = gerar_relatorio_geral_mensal(di, df, linhas, apenas_ativos)
    resp = HttpResponse(buffer, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="relatorio_geral_{di}_{df}.pdf"'
    return resp


# ---------- Usuários do sistema (apenas superusuário) ----------

@user_passes_test(eh_superusuario)
def lista_usuarios(request):
    usuarios = User.objects.all().order_by("username")
    return render(request, "core/lista_usuarios.html", {"usuarios": usuarios})


@user_passes_test(eh_superusuario)
def usuario_form_view(request, pk=None):
    usuario = get_object_or_404(User, pk=pk) if pk else None
    erro = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        senha = request.POST.get("password", "")
        is_staff = request.POST.get("is_staff") == "on"

        if not username:
            erro = "Informe um nome de usuário."
        elif User.objects.filter(username=username).exclude(pk=usuario.pk if usuario else None).exists():
            erro = "Já existe um usuário com esse nome."
        else:
            if usuario is None:
                if not senha:
                    erro = "Defina uma senha para o novo usuário."
                else:
                    usuario = User.objects.create_user(username=username, password=senha, first_name=first_name)
                    usuario.is_staff = is_staff
                    usuario.save()
                    messages.success(request, f"Usuário '{username}' criado com sucesso.")
                    return redirect("lista_usuarios")
            else:
                usuario.username = username
                usuario.first_name = first_name
                usuario.is_staff = is_staff
                if senha:
                    usuario.set_password(senha)
                usuario.save()
                messages.success(request, f"Usuário '{username}' atualizado com sucesso.")
                return redirect("lista_usuarios")

    return render(request, "core/usuario_form.html", {"usuario": usuario, "erro": erro})


@user_passes_test(eh_superusuario)
def usuario_excluir(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.is_superuser:
        messages.error(request, "Não é possível excluir um superusuário por aqui.")
        return redirect("lista_usuarios")
    if request.method == "POST":
        nome = usuario.username
        usuario.delete()
        messages.success(request, f"Usuário '{nome}' excluído.")
        return redirect("lista_usuarios")
    return render(request, "core/confirmar_exclusao.html", {"objeto": usuario, "tipo": "usuário"})
