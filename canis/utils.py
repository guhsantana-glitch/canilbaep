"""Resolução do canil atual da requisição (escopo multi-canil)."""

from .models import Canil


def canil_atual(request):
    """Retorna o Canil em que o usuário está operando, ou None.

    - Superusuário: canil escolhido no painel de gestão (sessão).
    - Demais: canil do seu vínculo ativo.
    """
    if not request.user.is_authenticated:
        return None
    if request.user.is_superuser:
        canil_id = request.session.get("canil_id")
        if not canil_id:
            return None
        return Canil.objects.filter(pk=canil_id).first()
    vinculo = getattr(request.user, "vinculo_canil", None)
    if vinculo is None or not vinculo.ativo:
        return None
    return vinculo.canil
