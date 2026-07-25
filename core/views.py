from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse

from .models import Cao, Condutor, Vacina, Medicamento, Pesagem, Treinamento, Documento
from .forms import (
    CaoForm, CondutorForm, VacinaForm, MedicamentoForm,
    PesagemForm, TreinamentoForm, DocumentoForm, RelatorioMensalForm,
)
from .pdf_utils import gerar_ficha_box, gerar_relatorio_mensal
from . import govbr


class CanilLoginView(LoginView):
    template_name = "core/login.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["govbr_disponivel"] = govbr.is_configured()
        return ctx


def govbr_login(request):
    """Redireciona o usuário para a tela de autenticação do gov.br."""
    if not govbr.is_configured():
        messages.error(request, "Login com gov.br ainda não foi configurado neste ambiente.")
        return redirect("login")
    return redirect(govbr.montar_url_autorizacao(request))


def govbr_callback(request):
    """Recebe o retorno do gov.br, valida state, troca code por token e loga o usuário."""
    erro = request.GET.get("error")
    if erro:
        messages.error(request, f"Falha na autenticação gov.br: {erro}")
        return redirect("login")

    code = request.GET.get("code")
    state_recebido = request.GET.get("state")
    state_esperado = request.session.get("govbr_state")
    code_verifier = request.session.get("govbr_code_verifier")

    if not code or not state_recebido or state_recebido != state_esperado:
        return HttpResponseBadRequest("Requisição inválida ou expirada. Tente novamente.")

    try:
        token_data = govbr.trocar_code_por_token(code, code_verifier)
        userinfo = govbr.obter_userinfo(token_data["access_token"])
    except Exception:
        messages.error(request, "Não foi possível concluir a autenticação com o gov.br. Tente novamente.")
        return redirect("login")

    cpf = userinfo.get("sub")
    nome = userinfo.get("name", cpf)
    email = userinfo.get("email", "")

    user, criado = User.objects.get_or_create(
        username=cpf,
        defaults={"first_name": nome, "email": email},
    )
    if criado:
        user.set_unusable_password()
        user.save()
        messages.info(request, "Primeiro acesso via gov.br. Um administrador precisa vincular seu usuário a um Condutor, se aplicável.")

    for chave in ("govbr_state", "govbr_nonce", "govbr_code_verifier"):
        request.session.pop(chave, None)

    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("lista_caes")


def govbr_logout(request):
    """Encerra a sessão local e, se configurado, também a sessão no gov.br."""
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    if govbr.is_configured():
        retorno = request.build_absolute_uri(reverse("login"))
        return redirect(govbr.montar_url_logout(retorno))
    return redirect("login")



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
    return render(request, "core/ficha_cao.html", {
        "cao": cao,
        "pesagens": cao.pesagens.all()[:30],
        "vacinas": cao.vacinas.all(),
        "medicamentos": cao.medicamentos.all(),
        "treinamentos": cao.treinamentos.all(),
        "documentos": cao.documentos.all(),
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


@login_required
def vacina_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Vacina, VacinaForm, "core/registro_form.html")


@login_required
def medicamento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Medicamento, MedicamentoForm, "core/registro_form.html")


@login_required
def pesagem_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Pesagem, PesagemForm, "core/registro_form.html")


@login_required
def treinamento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Treinamento, TreinamentoForm, "core/registro_form.html")


@login_required
def documento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Documento, DocumentoForm, "core/registro_form.html")


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


# ---------- Relatório mensal ----------

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
