from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from canis.models import Canil, Pelotao, Unidade, VinculoUsuario
from canis.senhas import SENHA_PADRAO, gerar_senha_aleatoria
from core.models import Cao
from .forms import CanilForm, UnidadeForm


def eh_gestor(user):
    return user.is_authenticated and user.is_superuser


gestor_required = user_passes_test(eh_gestor, login_url="/login/")


@gestor_required
def painel(request):
    canis = Canil.objects.all().order_by("nome")
    total_caes = Cao.objects.count()
    total_usuarios = User.objects.filter(is_superuser=False).count()
    linhas = []
    for canil in canis:
        linhas.append({
            "canil": canil,
            "caes": Cao.objects.filter(canil=canil).count(),
            "usuarios": VinculoUsuario.objects.filter(canil=canil, ativo=True).count(),
        })
    return render(request, "gestaocanis/painel.html", {
        "canis": canis,
        "linhas": linhas,
        "total_canis": canis.count(),
        "total_ativos": canis.filter(ativo=True).count(),
        "total_unidades": Unidade.objects.count(),
        "total_caes": total_caes,
        "total_usuarios": total_usuarios,
        "canil_em_uso": request.session.get("canil_id"),
    })


# ---------- Unidades ----------

@gestor_required
def lista_unidades(request):
    unidades = Unidade.objects.all().order_by("nome")
    linhas = []
    for unidade in unidades:
        linhas.append({
            "unidade": unidade,
            "canis": unidade.canis.count(),
        })
    return render(request, "gestaocanis/lista_unidades.html", {"linhas": linhas})


@gestor_required
def unidade_form_view(request, pk=None):
    unidade = get_object_or_404(Unidade, pk=pk) if pk else None
    if request.method == "POST":
        form = UnidadeForm(request.POST, instance=unidade)
        if form.is_valid():
            unidade = form.save()
            messages.success(request, f"Unidade '{unidade.nome}' salva com sucesso.")
            return redirect("gestao_unidades")
    else:
        form = UnidadeForm(instance=unidade)
    return render(request, "gestaocanis/unidade_form.html", {"form": form, "unidade": unidade})


@gestor_required
def unidade_excluir(request, pk):
    unidade = get_object_or_404(Unidade, pk=pk)
    if unidade.canis.exists():
        messages.error(request, "Não é possível excluir: há canis vinculados a esta unidade. Desative-a em vez disso.")
        return redirect("gestao_unidades")
    if request.method == "POST":
        nome = unidade.nome
        unidade.delete()
        messages.success(request, f"Unidade '{nome}' excluída.")
        return redirect("gestao_unidades")
    return render(request, "core/confirmar_exclusao.html", {"objeto": unidade, "tipo": "unidade"})


@gestor_required
def canil_form_view(request, pk=None):
    canil = get_object_or_404(Canil, pk=pk) if pk else None
    if request.method == "POST":
        form = CanilForm(request.POST, instance=canil)
        if form.is_valid():
            canil = form.save()
            messages.success(request, f"Canil '{canil.nome}' salvo com sucesso.")
            return redirect("gestao_painel")
    else:
        form = CanilForm(instance=canil)
    return render(request, "gestaocanis/canil_form.html", {"form": form, "canil": canil})


@gestor_required
def canil_excluir(request, pk):
    canil = get_object_or_404(Canil, pk=pk)
    if Cao.objects.filter(canil=canil).exists() or VinculoUsuario.objects.filter(canil=canil).exists():
        messages.error(request, "Não é possível excluir: há cães ou usuários vinculados a este canil. Desative-o em vez disso.")
        return redirect("gestao_painel")
    if request.method == "POST":
        nome = canil.nome
        canil.delete()
        if request.session.get("canil_id") == pk:
            request.session.pop("canil_id")
        messages.success(request, f"Canil '{nome}' excluído.")
        return redirect("gestao_painel")
    return render(request, "core/confirmar_exclusao.html", {"objeto": canil, "tipo": "canil"})


@gestor_required
def acessar_canil(request, pk):
    canil = get_object_or_404(Canil, pk=pk)
    if not canil.ativo:
        messages.error(request, "Este canil está desativado.")
        return redirect("gestao_painel")
    request.session["canil_id"] = canil.pk
    messages.success(request, f"Operando agora no canil '{canil.nome}'.")
    return redirect("lista_caes")


@gestor_required
def sair_canil(request):
    request.session.pop("canil_id", None)
    return redirect("gestao_painel")


# ---------- Pelotões (por canil) ----------

@gestor_required
def lista_pelotoes(request, canil_pk):
    canil = get_object_or_404(Canil, pk=canil_pk)
    pelotoes = canil.pelotoes.order_by("nome")
    linhas = []
    for pelotao in pelotoes:
        linhas.append({
            "pelotao": pelotao,
            "condutores": pelotao.condutores.filter(ativo=True).count(),
            "usuarios": pelotao.vinculos.filter(ativo=True).count(),
        })
    return render(request, "gestaocanis/lista_pelotoes.html", {"canil": canil, "linhas": linhas})


@gestor_required
def pelotao_form_view(request, canil_pk, pk=None):
    canil = get_object_or_404(Canil, pk=canil_pk)
    pelotao = get_object_or_404(Pelotao, pk=pk, canil=canil) if pk else None
    erro = None
    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        ativo = request.POST.get("ativo") == "on"
        if not nome:
            erro = "Informe o nome do pelotão."
        elif Pelotao.objects.filter(canil=canil, nome=nome).exclude(pk=pelotao.pk if pelotao else None).exists():
            erro = "Já existe um pelotão com esse nome neste canil."
        else:
            if pelotao is None:
                Pelotao.objects.create(canil=canil, nome=nome, ativo=ativo)
                messages.success(request, f"Pelotão '{nome}' criado com sucesso.")
            else:
                pelotao.nome = nome
                pelotao.ativo = ativo
                pelotao.save()
                messages.success(request, f"Pelotão '{nome}' atualizado.")
            return redirect("gestao_pelotoes", canil_pk=canil.pk)
    return render(request, "gestaocanis/pelotao_form.html", {
        "canil": canil, "pelotao": pelotao, "erro": erro,
    })


@gestor_required
def pelotao_excluir(request, canil_pk, pk):
    canil = get_object_or_404(Canil, pk=canil_pk)
    pelotao = get_object_or_404(Pelotao, pk=pk, canil=canil)
    if pelotao.condutores.exists() or pelotao.vinculos.exists():
        messages.error(request, "Não é possível excluir: há condutores ou usuários vinculados a este pelotão. Desative-o em vez disso.")
        return redirect("gestao_pelotoes", canil_pk=canil.pk)
    if request.method == "POST":
        nome = pelotao.nome
        pelotao.delete()
        messages.success(request, f"Pelotão '{nome}' excluído.")
        return redirect("gestao_pelotoes", canil_pk=canil.pk)
    return render(request, "core/confirmar_exclusao.html", {"objeto": pelotao, "tipo": "pelotão"})


# ---------- Usuários dos canis ----------

@gestor_required
def lista_usuarios_canis(request):
    vinculos = VinculoUsuario.objects.select_related("usuario", "canil", "pelotao").order_by("canil__nome", "usuario__username")
    return render(request, "gestaocanis/lista_usuarios.html", {"vinculos": vinculos})


@gestor_required
def usuario_form_view(request, pk=None):
    vinculo = get_object_or_404(VinculoUsuario, pk=pk) if pk else None
    usuario = vinculo.usuario if vinculo else None
    canis = Canil.objects.filter(ativo=True).order_by("nome")
    pelotoes = Pelotao.objects.filter(ativo=True).select_related("canil").order_by("canil__nome", "nome")
    erro = None
    dados = {"username": "", "first_name": "", "canil_id": "", "papel": "operador", "ativo": True, "pelotao_id": ""}
    if vinculo:
        dados = {"username": usuario.username, "first_name": usuario.first_name,
                 "canil_id": str(vinculo.canil_id), "papel": vinculo.papel, "ativo": vinculo.ativo,
                 "pelotao_id": str(vinculo.pelotao_id or "")}
    if request.method == "POST":
        dados = {"username": request.POST.get("username", "").strip(),
                 "first_name": request.POST.get("first_name", "").strip(),
                 "canil_id": request.POST.get("canil", ""),
                 "papel": request.POST.get("papel", "operador"),
                 "ativo": request.POST.get("ativo") == "on",
                 "pelotao_id": request.POST.get("pelotao", "")}
        senha = request.POST.get("password", "").strip()
        canil = Canil.objects.filter(pk=dados["canil_id"]).first()
        pelotao = Pelotao.objects.filter(pk=dados["pelotao_id"], canil=canil, ativo=True).first() if canil else None
        if not dados["username"]:
            erro = "Informe um nome de usuário."
        elif not canil:
            erro = "Selecione um canil ativo."
        elif dados["papel"] == "operador" and pelotao is None:
            erro = "Operadores precisam de um pelotão atribuído."
        elif User.objects.filter(username=dados["username"]).exclude(pk=usuario.pk if usuario else None).exists():
            erro = "Já existe um usuário com esse nome."
        else:
            if usuario is None:
                # Em branco: gera aleatória. Padrão sugerido: canil123.
                if not senha:
                    senha = gerar_senha_aleatoria()
                usuario = User.objects.create_user(
                    username=dados["username"], password=senha, first_name=dados["first_name"])
                VinculoUsuario.objects.create(
                    usuario=usuario, canil=canil, papel=dados["papel"],
                    pelotao=pelotao,
                    ativo=dados["ativo"], senha_temporaria=True,
                    senha_temporaria_em=timezone.now())
                return render(request, "gestaocanis/usuario_credenciais.html", {
                    "usuario": usuario, "canil": canil, "senha": senha, "novo": True,
                })
            else:
                usuario.username = dados["username"]
                usuario.first_name = dados["first_name"]
                if senha:
                    usuario.set_password(senha)
                    vinculo.senha_temporaria = True
                    vinculo.senha_temporaria_em = timezone.now()
                usuario.save()
                vinculo.canil = canil
                vinculo.papel = dados["papel"]
                vinculo.pelotao = pelotao if dados["papel"] == "operador" else None
                vinculo.ativo = dados["ativo"]
                vinculo.save()
                messages.success(request, f"Usuário '{usuario.username}' atualizado.")
            return redirect("gestao_usuarios")
    return render(request, "gestaocanis/usuario_form.html",
                  {"vinculo": vinculo, "usuario_obj": usuario, "canis": canis, "pelotoes": pelotoes,
                   "dados": dados, "erro": erro,
                   "papeis": VinculoUsuario.PAPEL_CHOICES, "senha_padrao": SENHA_PADRAO})


@gestor_required
def usuario_excluir(request, pk):
    vinculo = get_object_or_404(VinculoUsuario, pk=pk)
    if request.method == "POST":
        nome = vinculo.usuario.username
        vinculo.usuario.delete()
        messages.success(request, f"Usuário '{nome}' excluído.")
        return redirect("gestao_usuarios")
    return render(request, "core/confirmar_exclusao.html", {"objeto": vinculo.usuario, "tipo": "usuário"})


@gestor_required
def usuario_resetar_senha(request, pk):
    vinculo = get_object_or_404(VinculoUsuario, pk=pk)
    if request.method == "POST":
        senha = gerar_senha_aleatoria()
        vinculo.usuario.set_password(senha)
        vinculo.usuario.save()
        vinculo.senha_temporaria = True
        vinculo.senha_temporaria_em = timezone.now()
        vinculo.save()
        return render(request, "gestaocanis/usuario_credenciais.html", {
            "usuario": vinculo.usuario, "canil": vinculo.canil, "senha": senha, "novo": False,
        })
    return render(request, "gestaocanis/usuario_senha.html", {"vinculo": vinculo})


@gestor_required
def atualizar_banco(request):
    """Roda as migrations pelo navegador (plano free do Render não tem Shell).

    Uso: entre como superusuário e acesse /gestao/manutencao/atualizar-banco/
    Pode remover esta rota quando o migrate passar a rodar no deploy.
    """
    from django.core.management import call_command
    from django.http import HttpResponse
    from io import StringIO

    saida = StringIO()
    try:
        call_command("migrate", "--no-input", stdout=saida)
        texto = saida.getvalue() or "Migrations aplicadas."
        return HttpResponse(f"<h1>Banco atualizado</h1><pre>{texto}</pre><p><a href='/'>Voltar ao sistema</a></p>")
    except Exception as exc:  # noqa: BLE001
        return HttpResponse(f"<h1>Falha ao migrar</h1><pre>{exc}</pre>", status=500)
