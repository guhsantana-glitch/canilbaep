from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from functools import wraps

from canis.utils import canil_atual

from .models import (
    Cao, Condutor, Vacina, Medicamento, Pesagem, Treinamento, Documento,
    Veterinario, TipoVacina, Vermifugacao, Ectoparasita, OcorrenciaSaude,
    VisitaTecnica, OcorrenciaPolicial,
)
from .forms import (
    CaoForm, CondutorForm, VacinaForm, MedicamentoForm,
    PesagemForm, TreinamentoForm, DocumentoForm, RelatorioMensalForm, RelatorioGeralForm,
    VeterinarioForm, TipoVacinaForm, VermifugacaoForm, EctoparasitaForm,
    OcorrenciaSaudeForm, VisitaTecnicaForm, OcorrenciaPolicialForm,
)
from .pdf_utils import gerar_ficha_box, gerar_relatorio_mensal, gerar_relatorio_geral_mensal, gerar_ficha_sanitaria, gerar_produtividade_mensal


class CanilLoginView(LoginView):
    template_name = "core/login.html"

    def get_success_url(self):
        # Gestor geral abre o sistema de gestão; operador abre o canil.
        if self.request.user.is_superuser:
            return reverse("gestao_painel")
        return reverse("lista_caes")


class CanilLogoutView(LogoutView):
    next_page = "login"


def eh_superusuario(user):
    return user.is_superuser


@login_required
def trocar_senha_obrigatoria(request):
    """Primeiro acesso: o usuário define sua senha definitiva.

    Prazo de 7 dias a partir da emissão: vencido o prazo, a troca por
    aqui é bloqueada e o usuário deve falar com o desenvolvedor."""
    from canis.senhas import (
        PRAZO_TROCA_SENHA_DIAS, dias_restantes_senha,
        limite_troca_senha, senha_temporaria_expirada,
    )

    vinculo = getattr(request.user, "vinculo_canil", None)
    if vinculo is not None and vinculo.senha_temporaria and senha_temporaria_expirada(vinculo):
        return redirect("conta_bloqueada")
    limite = limite_troca_senha(vinculo) if vinculo is not None else None
    dias_restantes = dias_restantes_senha(vinculo) if vinculo is not None else 0
    contexto = {
        "prazo_dias": PRAZO_TROCA_SENHA_DIAS,
        "limite": limite,
        "dias_restantes": dias_restantes,
        "tem_prazo": bool(vinculo is not None and vinculo.senha_temporaria),
    }
    if request.method == "POST":
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as ValidacaoErro
        from django.contrib.auth import update_session_auth_hash

        nova_senha = request.POST.get("nova_senha", "")
        confirmar_senha = request.POST.get("confirmar_senha", "")
        if not nova_senha:
            messages.error(request, "Informe a nova senha.")
        elif nova_senha != confirmar_senha:
            messages.error(request, "As senhas não coincidem.")
        else:
            try:
                validate_password(nova_senha, request.user)
            except ValidacaoErro as erros:
                for erro in erros.messages:
                    messages.error(request, erro)
                return render(request, "core/trocar_senha.html", contexto)
            request.user.set_password(nova_senha)
            request.user.save()
            if vinculo is not None:
                vinculo.senha_temporaria = False
                vinculo.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Senha alterada com sucesso! Bem-vindo ao sistema.")
            return redirect("lista_caes")
    return render(request, "core/trocar_senha.html", contexto)


def conta_bloqueada(request):
    """Conta bloqueada por não trocar a senha temporária em 7 dias.

    Encerra a sessão (se houver) e exibe popup pedindo contato com o
    desenvolvedor. Rota isenta dos middlewares de canil/senha."""
    from django.contrib.auth import logout

    if request.user.is_authenticated:
        logout(request)
    return render(request, "core/conta_bloqueada.html")


def exigir_canil(view):
    """Garante que o usuário esteja operando dentro de um canil.

    Superusuário sem canil escolhido é enviado ao painel de gestão.
    """
    @wraps(view)
    @login_required
    def _wrapper(request, *args, **kwargs):
        canil = canil_atual(request)
        if canil is None:
            if request.user.is_superuser:
                messages.info(request, "Selecione um canil para operar.")
                return redirect("gestao_painel")
            return render(request, "canis/sem_acesso.html", status=403)
        request.canil_escopo = canil
        return view(request, *args, **kwargs)
    return _wrapper


def _form(FormClass, canil, *args, pelotao=None, **kwargs):
    """Instancia o form passando canil e/ou pelotão quando suportados."""
    try:
        return FormClass(*args, canil=canil, pelotao=pelotao, **kwargs)
    except TypeError:
        try:
            return FormClass(*args, canil=canil, **kwargs)
        except TypeError:
            return FormClass(*args, **kwargs)


def _qs(model, request):
    """Queryset do modelo já filtrado pelo canil em operação."""
    return model.objects.filter(canil=request.canil_escopo)


def _escopo_pelotao(request):
    """Restrição por pelotão do usuário.

    None  → sem restrição (superusuário ou administrador do canil)
    Pelotao → restrito a esse pelotão
    False → nenhum dado visível (operador sem pelotão atribuído)
    """
    user = request.user
    if user.is_superuser:
        return None
    vinculo = getattr(user, "vinculo_canil", None)
    if vinculo is None or vinculo.papel == "admin_canil":
        return None
    if vinculo.pelotao_id is None:
        return False
    return vinculo.pelotao


def _q_pelotao(request, prefix=""):
    """Filtro Q de restrição por pelotão para querysets de cães.

    A visibilidade usa o pelotão do próprio cão (Cao.pelotao).
    prefix: caminho até o cão em querysets de objetos vinculados
    (ex.: prefix="cao__" para ocorrências policiais).
    """
    escopo = _escopo_pelotao(request)
    if escopo is None:
        return Q()
    if escopo is False:
        return Q(pk__in=[])
    return Q(**{f"{prefix}pelotao_id": escopo.pk})


def _q_condutor_pelotao(request):
    """Filtro Q de restrição por pelotão para querysets de condutores."""
    escopo = _escopo_pelotao(request)
    if escopo is None:
        return Q()
    if escopo is False:
        return Q(pk__in=[])
    return Q(pelotao_id=escopo.pk)


def _fmt_qtd(v):
    """Formata quantidade em estilo pt-BR (vírgula decimal, sem zeros à direita)."""
    from decimal import Decimal
    s = format(Decimal(v).normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _drogas_convertidas(qs):
    """Agrega as drogas das ocorrências convertendo as unidades para gramas.

    KG é multiplicado por 1000; G entra como está; UN (porções/pinos/pedras)
    não tem massa padrão e é contada separadamente.
    """
    from decimal import Decimal
    from django.db.models import Case, DecimalField, F, Sum, Value, When

    linhas = (
        qs.exclude(droga_tipo="NA")
        .exclude(droga_quantidade__isnull=True)
        .annotate(
            qtd_g=Case(
                When(droga_unidade="KG", then=F("droga_quantidade") * Value(1000)),
                When(droga_unidade="G", then=F("droga_quantidade")),
                default=Value(0),
                output_field=DecimalField(max_digits=13, decimal_places=3),
            ),
            qtd_un=Case(
                When(droga_unidade="UN", then=F("droga_quantidade")),
                default=Value(0),
                output_field=DecimalField(max_digits=13, decimal_places=3),
            ),
        )
        .values("droga_tipo")
        .annotate(total_g=Sum("qtd_g"), total_un=Sum("qtd_un"))
        .order_by("droga_tipo")
    )
    drogas = []
    for d in linhas:
        total_g = d["total_g"] or 0
        total_un = d["total_un"] or 0
        if not total_g and not total_un:
            continue
        partes = []
        if total_g:
            partes.append(f"{_fmt_qtd(total_g)} g")
            if total_g >= 1000:
                partes.append(f"({_fmt_qtd(Decimal(total_g) / 1000)} kg)")
        if total_un:
            partes.append(f"+ {_fmt_qtd(total_un)} un")
        drogas.append({
            "droga_tipo": d["droga_tipo"],
            "droga_tipo_display": dict(OcorrenciaPolicial.DrogaTipo.choices).get(d["droga_tipo"], d["droga_tipo"]),
            "total_g": total_g,
            "total_un": total_un,
            "resumo": " ".join(partes),
        })
    return drogas


def _sem_pelotao(request):
    """True quando é operador sem pelotão atribuído (para avisos na UI)."""
    return _escopo_pelotao(request) is False


def _get(model, request, pk, **kwargs):
    if model is Cao:
        return get_object_or_404(
            Cao.objects.filter(_q_pelotao(request)),
            pk=pk, canil=request.canil_escopo, **kwargs,
        )
    return get_object_or_404(model, pk=pk, canil=request.canil_escopo, **kwargs)


# ---------- Cães ----------

@exigir_canil
def lista_caes(request):
    caes = Cao.objects.select_related("pelotao", "condutor_atual").filter(
        canil=request.canil_escopo
    ).filter(_q_pelotao(request))
    if _sem_pelotao(request):
        messages.warning(request, "Seu usuário não possui pelotão atribuído. Contate o administrador do canil.")
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


@exigir_canil
def ficha_cao(request, pk):
    cao = _get(Cao, request, pk)
    treinamentos = cao.treinamentos.all()
    evolucao = [
        {"data": t.data.strftime("%d/%m/%Y"), "nota": float(t.nota_avaliacao)}
        for t in treinamentos.exclude(nota_avaliacao__isnull=True).order_by("data")
    ]
    pesagens_qs = cao.pesagens.all()
    evolucao_peso = [
        {"data": p.data.strftime("%d/%m/%Y"), "peso": float(p.peso_kg)}
        for p in pesagens_qs.order_by("data")
    ]
    return render(request, "core/ficha_cao.html", {
        "cao": cao,
        "hoje": timezone.now().date(),
        "pesagens": pesagens_qs[:30],
        "vacinas": cao.vacinas.select_related("tipo", "veterinario").all(),
        "vermifugacoes": cao.vermifugacoes.select_related("veterinario").all(),
        "ectoparasitas": cao.ectoparasitas.select_related("veterinario").all(),
        "ocorrencias_saude": cao.ocorrencias_saude.select_related("veterinario").all(),
        "visitas_tecnicas": cao.visitas_tecnicas.all(),
        "medicamentos": cao.medicamentos.select_related("veterinario").all(),
        "treinamentos": treinamentos,
        "documentos": cao.documentos.all(),
        "ocorrencias_policiais": cao.ocorrencias_policiais.select_related("condutor").all(),
        "evolucao_json": evolucao,
        "evolucao_peso_json": evolucao_peso,
    })


@exigir_canil
def cao_form_view(request, pk=None):
    canil = request.canil_escopo
    cao = _get(Cao, request, pk) if pk else None
    escopo = _escopo_pelotao(request)
    if request.method == "POST":
        form = _form(CaoForm, canil, request.POST, request.FILES, instance=cao,
                     pelotao=escopo)
        if form.is_valid():
            cao = form.save(commit=False)
            cao.canil = canil
            # Sem pelotão escolhido, herda o do condutor selecionado
            if cao.pelotao_id is None and cao.condutor_atual_id:
                cao.pelotao = cao.condutor_atual.pelotao
            cao.save()
            messages.success(request, f"Cão '{cao.nome}' salvo com sucesso.")
            return redirect("ficha_cao", pk=cao.pk)
    else:
        inicial = {}
        if cao is None and escopo is not None and escopo is not False:
            inicial["pelotao"] = escopo
        form = _form(CaoForm, canil, instance=cao, pelotao=escopo, initial=inicial)
    return render(request, "core/cao_form.html", {"form": form, "cao": cao})


@exigir_canil
def cao_excluir(request, pk):
    cao = _get(Cao, request, pk)
    if request.method == "POST":
        nome = cao.nome
        cao.delete()
        messages.success(request, f"Cão '{nome}' excluído.")
        return redirect("lista_caes")
    return render(request, "core/confirmar_exclusao.html", {"objeto": cao, "tipo": "cão"})


@exigir_canil
def cao_ficha_pdf(request, pk):
    cao = _get(Cao, request, pk)
    buffer = gerar_ficha_box(cao)
    resp = HttpResponse(buffer, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="ficha_box_{cao.nome}.pdf"'
    return resp


@exigir_canil
def cao_ficha_sanitaria_pdf(request, pk):
    """Ficha Sanitária oficial do 10º BAEP (imunização, vermifugação, peso,
    ectoparasitas, ocorrências de saúde e visitas técnicas)."""
    cao = _get(Cao, request, pk)
    buffer = gerar_ficha_sanitaria(cao)
    resp = HttpResponse(buffer, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="ficha_sanitaria_{cao.nome}.pdf"'
    return resp


# ---------- Registros vinculados ao cão (vacina, medicamento, pesagem, treinamento, documento) ----------

def _registro_form_view(request, pk, cao_pk, Model, FormClass, template, campo_cao="cao"):
    cao = _get(Cao, request, cao_pk)
    instancia = get_object_or_404(Model, pk=pk, cao=cao) if pk else None
    if request.method == "POST":
        form = _form(FormClass, request.canil_escopo, request.POST, request.FILES, instance=instancia)
        if form.is_valid():
            obj = form.save(commit=False)
            setattr(obj, campo_cao, cao)
            obj.save()
            messages.success(request, "Registro salvo com sucesso.")
            return redirect("ficha_cao", pk=cao.pk)
    else:
        form = _form(FormClass, request.canil_escopo, instance=instancia)
    return render(request, template, {"form": form, "cao": cao})


def _registro_excluir_view(request, cao_pk, pk, Model):
    cao = _get(Cao, request, cao_pk)
    obj = get_object_or_404(Model, pk=pk, cao=cao)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Registro excluído.")
        return redirect("ficha_cao", pk=cao.pk)
    return render(request, "core/confirmar_exclusao.html", {"objeto": obj, "tipo": "registro"})


@exigir_canil
def vacina_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Vacina, VacinaForm, "core/registro_form.html")


@exigir_canil
def vacina_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Vacina)


@exigir_canil
def medicamento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Medicamento, MedicamentoForm, "core/registro_form.html")


@exigir_canil
def medicamento_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Medicamento)


@exigir_canil
def pesagem_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Pesagem, PesagemForm, "core/registro_form.html")


@exigir_canil
def pesagem_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Pesagem)


@exigir_canil
def treinamento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Treinamento, TreinamentoForm, "core/registro_form.html")


@exigir_canil
def treinamento_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Treinamento)


@exigir_canil
def documento_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Documento, DocumentoForm, "core/registro_form.html")


@exigir_canil
def documento_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Documento)


# ---------- Ficha Sanitária (vermifugação, ectoparasitas, saúde, visitas) ----------

@exigir_canil
def vermifugacao_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Vermifugacao, VermifugacaoForm, "core/registro_form.html")


@exigir_canil
def vermifugacao_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Vermifugacao)


@exigir_canil
def ectoparasita_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, Ectoparasita, EctoparasitaForm, "core/registro_form.html")


@exigir_canil
def ectoparasita_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, Ectoparasita)


@exigir_canil
def ocorrencia_saude_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, OcorrenciaSaude, OcorrenciaSaudeForm, "core/registro_form.html")


@exigir_canil
def ocorrencia_saude_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, OcorrenciaSaude)


@exigir_canil
def visita_tecnica_form_view(request, cao_pk, pk=None):
    return _registro_form_view(request, pk, cao_pk, VisitaTecnica, VisitaTecnicaForm, "core/registro_form.html")


@exigir_canil
def visita_tecnica_excluir(request, cao_pk, pk):
    return _registro_excluir_view(request, cao_pk, pk, VisitaTecnica)


# ---------- Ocorrências policiais (F01 / J09 / G01) ----------

@exigir_canil
def lista_ocorrencias(request):
    from datetime import date
    from django.db.models import Sum, Count

    MESES_PT = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ]

    canil = request.canil_escopo
    if _sem_pelotao(request):
        messages.warning(request, "Seu usuário não possui pelotão atribuído. Contate o administrador do canil.")
    ocorrencias = (
        OcorrenciaPolicial.objects
        .select_related("cao", "condutor")
        .filter(cao__canil=canil)
        .filter(_q_pelotao(request, prefix="cao__"))
    )
    tipo = request.GET.get("tipo")
    busca = request.GET.get("q", "").strip()
    if tipo:
        ocorrencias = ocorrencias.filter(tipo=tipo)
    if busca:
        ocorrencias = ocorrencias.filter(
            Q(cao__nome__icontains=busca)
            | Q(numero_bo__icontains=busca)
            | Q(local__icontains=busca)
            | Q(prefixo_viatura__icontains=busca)
        )
    # Totais do filtro atual (para o cabeçalho da página)
    totais = ocorrencias.aggregate(
        total_armas=Sum("qtd_armas"),
        total_procurados=Sum("qtd_procurados"),
    )

    # ---------- Produtividade mensal (filtro por cão + mês) ----------
    hoje = date.today()
    try:
        mes = int(request.GET.get("mes", hoje.month))
        ano = int(request.GET.get("ano", hoje.year))
    except (TypeError, ValueError):
        mes, ano = hoje.month, hoje.year
    if mes < 1 or mes > 12:
        mes = hoje.month
    cao_id = request.GET.get("cao", "").strip()
    prod_qs = OcorrenciaPolicial.objects.select_related("cao", "condutor").filter(
        cao__canil=canil, data__year=ano, data__month=mes,
    ).filter(_q_pelotao(request, prefix="cao__"))
    cao_prod = None
    if cao_id:
        try:
            cao_prod = Cao.objects.filter(_q_pelotao(request)).get(pk=int(cao_id), canil=canil)
            prod_qs = prod_qs.filter(cao=cao_prod)
        except (ValueError, Cao.DoesNotExist):
            cao_id = ""
    prod_qs = prod_qs.order_by("data", "id")
    prod_totais_qs = prod_qs.aggregate(
        total_armas=Sum("qtd_armas"), total_procurados=Sum("qtd_procurados"),
    )
    prod_totais = {
        "total_ocorrencias": prod_qs.count(),
        "total_armas": prod_totais_qs["total_armas"] or 0,
        "total_procurados": prod_totais_qs["total_procurados"] or 0,
    }
    por_tipo_qs = prod_qs.values("tipo").annotate(n=Count("id"))
    por_tipo = {"F01": 0, "J09": 0, "G01": 0}
    for linha in por_tipo_qs:
        por_tipo[linha["tipo"]] = linha["n"]
    drogas = _drogas_convertidas(prod_qs)
    anos_disponiveis = list(range(hoje.year - 5, hoje.year + 2))
    meses = [(i, MESES_PT[i - 1]) for i in range(1, 13)]

    return render(request, "core/lista_ocorrencias.html", {
        "ocorrencias": ocorrencias[:200],
        "tipo_choices": OcorrenciaPolicial.Tipo.choices,
        "tipo_selecionado": tipo or "",
        "busca": busca,
        "totais": totais,
        # produtividade
        "caes": Cao.objects.filter(canil=canil).filter(_q_pelotao(request)).select_related("pelotao", "condutor_atual").order_by("nome"),
        "mes": mes, "ano": ano, "meses": meses, "anos_disponiveis": anos_disponiveis,
        "cao_prod_id": cao_id, "cao_prod": cao_prod,
        "prod_ocorrencias": prod_qs[:200],
        "prod_totais": prod_totais, "prod_por_tipo": por_tipo, "prod_drogas": drogas,
    })


@exigir_canil
def produtividade_mensal_pdf(request):
    from datetime import date
    from django.db.models import Sum, Count

    canil = request.canil_escopo
    hoje = date.today()
    try:
        mes = int(request.GET.get("mes", hoje.month))
        ano = int(request.GET.get("ano", hoje.year))
    except (TypeError, ValueError):
        mes, ano = hoje.month, hoje.year
    cao_id = request.GET.get("cao", "").strip()
    qs = OcorrenciaPolicial.objects.select_related("cao", "condutor").filter(
        cao__canil=canil, data__year=ano, data__month=mes,
    ).filter(_q_pelotao(request, prefix="cao__"))
    cao_nome = "Todos os cães"
    if cao_id:
        cao_obj = get_object_or_404(
            Cao.objects.filter(_q_pelotao(request)), pk=cao_id, canil=canil
        )
        qs = qs.filter(cao=cao_obj)
        cao_nome = cao_obj.nome
    qs = qs.order_by("data", "id")
    agg = qs.aggregate(total_armas=Sum("qtd_armas"), total_procurados=Sum("qtd_procurados"))
    totais = {"total_ocorrencias": qs.count(), "total_armas": agg["total_armas"] or 0,
              "total_procurados": agg["total_procurados"] or 0}
    por_tipo = {"F01": 0, "J09": 0, "G01": 0}
    for linha in qs.values("tipo").annotate(n=Count("id")):
        por_tipo[linha["tipo"]] = linha["n"]
    drogas = _drogas_convertidas(qs)
    buffer = gerar_produtividade_mensal(
        canil.nome if hasattr(canil, "nome") else str(canil),
        mes, ano, cao_nome, list(qs), totais, por_tipo, drogas,
    )
    resp = HttpResponse(buffer, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="produtividade_{ano}_{mes:02d}.pdf"'
    return resp


@exigir_canil
def ocorrencia_policial_form_view(request, pk=None, cao_pk=None):
    """Form global (/ocorrencias/nova/) ou vinculado ao cão (/caes/<cao_pk>/...)."""
    canil = request.canil_escopo
    cao_fixo = _get(Cao, request, cao_pk) if cao_pk else None
    if pk:
        if cao_fixo:
            instancia = get_object_or_404(OcorrenciaPolicial, pk=pk, cao=cao_fixo)
        else:
            instancia = get_object_or_404(
                OcorrenciaPolicial.objects.filter(_q_pelotao(request, prefix="cao__")),
                pk=pk, cao__canil=canil,
            )
    else:
        instancia = None
    if request.method == "POST":
        form = _form(OcorrenciaPolicialForm, canil, request.POST, instance=instancia,
                     pelotao=_escopo_pelotao(request))
        if form.is_valid():
            obj = form.save(commit=False)
            if cao_fixo:
                obj.cao = cao_fixo
            # Segurança multi-canil: o cão precisa ser do canil em operação
            if obj.cao.canil_id != canil.pk:
                messages.error(request, "Cão de outro canil.")
                return redirect("lista_ocorrencias")
            # Segurança por pelotão: o cão precisa estar no escopo do usuário
            if not Cao.objects.filter(_q_pelotao(request)).filter(pk=obj.cao_id, canil=canil).exists():
                messages.error(request, "Cão de outro pelotão.")
                return redirect("lista_ocorrencias")
            obj.save()
            messages.success(request, "Ocorrência salva com sucesso.")
            if cao_fixo:
                return redirect("ficha_cao", pk=cao_fixo.pk)
            return redirect("lista_ocorrencias")
    else:
        inicial = {"cao": cao_fixo} if cao_fixo and instancia is None else None
        form = _form(OcorrenciaPolicialForm, canil, instance=instancia, initial=inicial,
                     pelotao=_escopo_pelotao(request))
    return render(request, "core/ocorrencia_form.html", {
        "form": form, "cao": cao_fixo or (instancia.cao if instancia else None),
        "editando": instancia is not None,
    })


@exigir_canil
def ocorrencia_policial_excluir(request, pk, cao_pk=None):
    canil = request.canil_escopo
    if cao_pk:
        cao = _get(Cao, request, cao_pk)
        obj = get_object_or_404(OcorrenciaPolicial, pk=pk, cao=cao)
        destino = ("ficha_cao", cao.pk)
    else:
        obj = get_object_or_404(
            OcorrenciaPolicial.objects.filter(_q_pelotao(request, prefix="cao__")),
            pk=pk, cao__canil=canil,
        )
        destino = ("lista_ocorrencias", None)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Ocorrência excluída.")
        if destino[0] == "ficha_cao":
            return redirect(destino[0], pk=destino[1])
        return redirect(destino[0])
    return render(request, "core/confirmar_exclusao.html", {"objeto": obj, "tipo": "ocorrência policial"})


# ---------- Condutores ----------

@exigir_canil
def lista_condutores(request):
    condutores = _qs(Condutor, request).select_related("pelotao").filter(_q_condutor_pelotao(request))
    return render(request, "core/lista_condutores.html", {"condutores": condutores})


@exigir_canil
def condutor_form_view(request, pk=None):
    condutor = _get(Condutor, request, pk) if pk else None
    if request.method == "POST":
        form = _form(CondutorForm, request.canil_escopo, request.POST, instance=condutor,
                     pelotao=_escopo_pelotao(request))
        if form.is_valid():
            condutor = form.save(commit=False)
            condutor.canil = request.canil_escopo
            escopo = _escopo_pelotao(request)
            if escopo is not None and escopo is not False:
                condutor.pelotao = escopo
            condutor.save()
            messages.success(request, "Condutor salvo com sucesso.")
            return redirect("lista_condutores")
    else:
        form = _form(CondutorForm, request.canil_escopo, instance=condutor,
                     pelotao=_escopo_pelotao(request))
    return render(request, "core/condutor_form.html", {"form": form, "condutor": condutor})


@exigir_canil
def condutor_excluir(request, pk):
    condutor = _get(Condutor, request, pk)
    if request.method == "POST":
        condutor.delete()
        messages.success(request, "Condutor excluído.")
        return redirect("lista_condutores")
    return render(request, "core/confirmar_exclusao.html", {"objeto": condutor, "tipo": "condutor"})


# ---------- Veterinários ----------

@exigir_canil
def lista_veterinarios(request):
    veterinarios = _qs(Veterinario, request)
    return render(request, "core/lista_veterinarios.html", {"veterinarios": veterinarios})


@exigir_canil
def veterinario_form_view(request, pk=None):
    veterinario = _get(Veterinario, request, pk) if pk else None
    if request.method == "POST":
        form = VeterinarioForm(request.POST, instance=veterinario)
        if form.is_valid():
            veterinario = form.save(commit=False)
            veterinario.canil = request.canil_escopo
            veterinario.save()
            messages.success(request, "Veterinário salvo com sucesso.")
            return redirect("lista_veterinarios")
    else:
        form = VeterinarioForm(instance=veterinario)
    return render(request, "core/veterinario_form.html", {"form": form, "veterinario": veterinario})


@exigir_canil
def veterinario_excluir(request, pk):
    veterinario = _get(Veterinario, request, pk)
    if request.method == "POST":
        veterinario.delete()
        messages.success(request, "Veterinário excluído.")
        return redirect("lista_veterinarios")
    return render(request, "core/confirmar_exclusao.html", {"objeto": veterinario, "tipo": "veterinário"})


# ---------- Tipos de vacina (catálogo) ----------

@exigir_canil
def lista_tipos_vacina(request):
    tipos = _qs(TipoVacina, request)
    return render(request, "core/lista_tipos_vacina.html", {"tipos": tipos})


@exigir_canil
def tipo_vacina_form_view(request, pk=None):
    tipo = _get(TipoVacina, request, pk) if pk else None
    if request.method == "POST":
        form = TipoVacinaForm(request.POST, instance=tipo)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.canil = request.canil_escopo
            tipo.save()
            messages.success(request, "Tipo de vacina salvo com sucesso.")
            return redirect("lista_tipos_vacina")
    else:
        form = TipoVacinaForm(instance=tipo)
    return render(request, "core/tipo_vacina_form.html", {"form": form, "tipo": tipo})


@exigir_canil
def tipo_vacina_excluir(request, pk):
    tipo = _get(TipoVacina, request, pk)
    if request.method == "POST":
        tipo.delete()
        messages.success(request, "Tipo de vacina excluído.")
        return redirect("lista_tipos_vacina")
    return render(request, "core/confirmar_exclusao.html", {"objeto": tipo, "tipo": "tipo de vacina"})


# ---------- Relatórios ----------

@exigir_canil
def relatorios_menu(request):
    return render(request, "core/relatorios_menu.html")


@exigir_canil
def relatorio_mensal(request):
    canil = request.canil_escopo
    resultado = None
    if request.method == "POST":
        form = _form(RelatorioMensalForm, canil, request.POST, pelotao=_escopo_pelotao(request))
        if form.is_valid():
            cao = form.cleaned_data["cao"]
            if cao.canil_id != canil.pk or not Cao.objects.filter(_q_pelotao(request)).filter(pk=cao.pk).exists():
                messages.error(request, "Cão de outro canil ou pelotão.")
                return redirect("relatorio_mensal")
            di = form.cleaned_data["data_inicio"]
            df = form.cleaned_data["data_fim"]
            resultado = {
                "cao": cao, "data_inicio": di, "data_fim": df,
                "pesagens": cao.pesagens.filter(data__range=(di, df)),
                "vacinas": cao.vacinas.filter(data_aplicacao__range=(di, df)),
                "medicamentos": cao.medicamentos.filter(data_inicio__range=(di, df)),
            }
    else:
        form = _form(RelatorioMensalForm, canil, pelotao=_escopo_pelotao(request))
    return render(request, "core/relatorio_mensal.html", {"form": form, "resultado": resultado})


@exigir_canil
def relatorio_mensal_pdf(request):
    canil = request.canil_escopo
    form = _form(RelatorioMensalForm, canil, request.GET, pelotao=_escopo_pelotao(request))
    if not form.is_valid():
        return redirect("relatorio_mensal")
    cao = form.cleaned_data["cao"]
    if cao.canil_id != canil.pk or not Cao.objects.filter(_q_pelotao(request)).filter(pk=cao.pk).exists():
        messages.error(request, "Cão de outro canil ou pelotão.")
        return redirect("relatorio_mensal")
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


def _montar_linhas_relatorio_geral(request, di, df, apenas_ativos):
    canil = request.canil_escopo
    caes = Cao.objects.select_related("pelotao", "condutor_atual").filter(
        canil=canil
    ).filter(_q_pelotao(request))
    if apenas_ativos:
        caes = caes.filter(status=Cao.Status.ATIVO)
    linhas = []
    for cao in caes.order_by("nome"):
        linhas.append({
            "nome": cao.nome,
            "box": cao.box,
            "condutor": cao.condutor_atual.nome if cao.condutor_atual else None,
            "pelotao": cao.pelotao.nome if cao.pelotao else None,
            "status": cao.get_status_display(),
            "peso_atual": cao.peso_atual(),
            "qtd_vacinas": cao.vacinas.filter(data_aplicacao__range=(di, df)).count(),
            "qtd_medicamentos": cao.medicamentos.filter(data_inicio__range=(di, df)).count(),
            "qtd_treinamentos": cao.treinamentos.filter(data__range=(di, df)).count(),
        })
    return linhas


@exigir_canil
def relatorio_geral(request):
    canil = request.canil_escopo
    resultado = None
    if request.method == "POST":
        form = RelatorioGeralForm(request.POST)
        if form.is_valid():
            di = form.cleaned_data["data_inicio"]
            df = form.cleaned_data["data_fim"]
            apenas_ativos = form.cleaned_data["apenas_ativos"]
            resultado = {
                "data_inicio": di, "data_fim": df, "apenas_ativos": apenas_ativos,
                "linhas": _montar_linhas_relatorio_geral(request, di, df, apenas_ativos),
            }
    else:
        form = RelatorioGeralForm(initial={"apenas_ativos": True})
    return render(request, "core/relatorio_geral.html", {"form": form, "resultado": resultado})


@exigir_canil
def relatorio_geral_pdf(request):
    canil = request.canil_escopo
    form = RelatorioGeralForm(request.GET)
    if not form.is_valid():
        return redirect("relatorio_geral")
    di = form.cleaned_data["data_inicio"]
    df = form.cleaned_data["data_fim"]
    apenas_ativos = form.cleaned_data["apenas_ativos"]
    linhas = _montar_linhas_relatorio_geral(request, di, df, apenas_ativos)
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
