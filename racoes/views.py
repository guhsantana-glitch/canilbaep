from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from core.views import exigir_canil
from .forms import RacaoForm, EntradaRacaoForm, SaidaRacaoForm
from .models import Racao, MovimentacaoRacao


@exigir_canil
def estoque(request):
    canil = request.canil_escopo
    racoes = Racao.objects.filter(canil=canil, ativo=True).order_by("nome")
    linhas = [{"racao": r, "estoque": r.estoque_kg(), "alerta": r.em_alerta()} for r in racoes]
    ultimas = MovimentacaoRacao.objects.filter(
        racao__canil=canil).select_related("racao", "responsavel")[:15]
    return render(request, "racoes/estoque.html", {"linhas": linhas, "ultimas": ultimas})


@exigir_canil
def racao_form_view(request, pk=None):
    canil = request.canil_escopo
    racao = get_object_or_404(Racao, pk=pk, canil=canil) if pk else None
    if request.method == "POST":
        form = RacaoForm(request.POST, instance=racao)
        if form.is_valid():
            racao = form.save(commit=False)
            racao.canil = canil
            racao.save()
            messages.success(request, f"Ração '{racao.nome}' salva com sucesso.")
            return redirect("racoes_estoque")
    else:
        form = RacaoForm(instance=racao)
    return render(request, "racoes/racao_form.html", {"form": form, "racao": racao})


@exigir_canil
def racao_excluir(request, pk):
    canil = request.canil_escopo
    racao = get_object_or_404(Racao, pk=pk, canil=canil)
    if racao.movimentacoes.exists():
        messages.error(request, "Não é possível excluir: há movimentações para esta ração. Desative-a em vez disso.")
        return redirect("racoes_estoque")
    if request.method == "POST":
        nome = racao.nome
        racao.delete()
        messages.success(request, f"Ração '{nome}' excluída.")
        return redirect("racoes_estoque")
    return render(request, "core/confirmar_exclusao.html", {"objeto": racao, "tipo": "ração"})


def _lancar(request, FormClass, tipo_mov, titulo, template_voltar="racoes_estoque"):
    canil = request.canil_escopo
    if request.method == "POST":
        form = FormClass(request.POST, canil=canil)
        if form.is_valid():
            mov = form.save(commit=False)
            mov.tipo = tipo_mov
            if tipo_mov == MovimentacaoRacao.Tipo.SAIDA and mov.quantidade_kg > mov.racao.estoque_kg():
                messages.error(
                    request,
                    f"Saída negada: estoque atual de '{mov.racao.nome}' é {mov.racao.estoque_kg()} kg.")
            else:
                mov.responsavel = request.user
                mov.save()
                messages.success(request, f"{mov.get_tipo_display()} de {mov.quantidade_kg} kg registrada.")
                return redirect(template_voltar)
    else:
        form = FormClass(canil=canil)
    return render(request, "racoes/movimentacao_form.html", {"form": form, "titulo": titulo})


@exigir_canil
def entrada_nova(request):
    return _lancar(request, EntradaRacaoForm, MovimentacaoRacao.Tipo.ENTRADA, "Registrar entrada")


@exigir_canil
def saida_nova(request):
    return _lancar(request, SaidaRacaoForm, MovimentacaoRacao.Tipo.SAIDA, "Registrar saída")


@exigir_canil
def extrato(request, pk):
    canil = request.canil_escopo
    racao = get_object_or_404(Racao, pk=pk, canil=canil)
    movs = racao.movimentacoes.select_related("responsavel").all()
    return render(request, "racoes/extrato.html", {
        "racao": racao, "movs": movs, "estoque": racao.estoque_kg(),
    })
