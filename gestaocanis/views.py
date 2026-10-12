from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from canis.models import Canil, Unidade, VinculoUsuario
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


# ---------- Usuários dos canis ----------

@gestor_required
def lista_usuarios_canis(request):
    vinculos = VinculoUsuario.objects.select_related("usuario", "canil").order_by("canil__nome", "usuario__username")
    return render(request, "gestaocanis/lista_usuarios.html", {"vinculos": vinculos})


@gestor_required
def usuario_form_view(request, pk=None):
    vinculo = get_object_or_404(VinculoUsuario, pk=pk) if pk else None
    usuario = vinculo.usuario if vinculo else None
    canis = Canil.objects.filter(ativo=True).order_by("nome")
    erro = None
    dados = {"username": "", "first_name": "", "canil_id": "", "papel": "operador", "ativo": True}
    if vinculo:
        dados = {"username": usuario.username, "first_name": usuario.first_name,
                 "canil_id": str(vinculo.canil_id), "papel": vinculo.papel, "ativo": vinculo.ativo}
    if request.method == "POST":
        dados = {"username": request.POST.get("username", "").strip(),
                 "first_name": request.POST.get("first_name", "").strip(),
                 "canil_id": request.POST.get("canil", ""),
                 "papel": request.POST.get("papel", "operador"),
                 "ativo": request.POST.get("ativo") == "on"}
        senha = request.POST.get("password", "")
        canil = Canil.objects.filter(pk=dados["canil_id"]).first()
        if not dados["username"]:
            erro = "Informe um nome de usuário."
        elif not canil:
            erro = "Selecione um canil ativo."
        elif User.objects.filter(username=dados["username"]).exclude(pk=usuario.pk if usuario else None).exists():
            erro = "Já existe um usuário com esse nome."
        elif usuario is None and not senha:
            erro = "Defina uma senha para o novo usuário."
        else:
            if usuario is None:
                usuario = User.objects.create_user(
                    username=dados["username"], password=senha, first_name=dados["first_name"])
                VinculoUsuario.objects.create(
                    usuario=usuario, canil=canil, papel=dados["papel"], ativo=dados["ativo"])
                messages.success(request, f"Usuário '{usuario.username}' criado no canil '{canil.nome}'.")
            else:
                usuario.username = dados["username"]
                usuario.first_name = dados["first_name"]
                if senha:
                    usuario.set_password(senha)
                usuario.save()
                vinculo.canil = canil
                vinculo.papel = dados["papel"]
                vinculo.ativo = dados["ativo"]
                vinculo.save()
                messages.success(request, f"Usuário '{usuario.username}' atualizado.")
            return redirect("gestao_usuarios")
    return render(request, "gestaocanis/usuario_form.html",
                  {"vinculo": vinculo, "usuario_obj": usuario, "canis": canis, "dados": dados, "erro": erro,
                   "papeis": VinculoUsuario.PAPEL_CHOICES})


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
        senha = request.POST.get("password", "").strip()
        if len(senha) < 4:
            messages.error(request, "A senha deve ter ao menos 4 caracteres.")
            return redirect("gestao_usuarios")
        vinculo.usuario.set_password(senha)
        vinculo.usuario.save()
        messages.success(request, f"Senha de '{vinculo.usuario.username}' redefinida.")
        return redirect("gestao_usuarios")
    return render(request, "gestaocanis/usuario_senha.html", {"vinculo": vinculo})
