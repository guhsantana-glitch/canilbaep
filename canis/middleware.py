from django.shortcuts import render, redirect

from .utils import canil_atual

ROTAS_ISENTAS = (
    "/login/",
    "/logout/",
    "/conta-bloqueada/",
    "/admin/",
    "/gestao/",
    "/static/",
    "/media/",
)


class CanilMiddleware:
    """Anexa o canil atual à requisição e bloqueia acessos irregulares.

    - Superusuário nunca é bloqueado (é o gestor geral).
    - Usuário sem vínculo ativo ou de canil desativado recebe 403.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.canil_atual = canil_atual(request)

        if request.path.startswith(ROTAS_ISENTAS):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.is_superuser:
            return self.get_response(request)

        vinculo = getattr(request.user, "vinculo_canil", None)
        if vinculo is None or not vinculo.ativo:
            return render(request, "canis/sem_acesso.html", status=403)

        if not vinculo.canil.ativo:
            return render(
                request,
                "canis/canil_inativo.html",
                {"canil": vinculo.canil},
                status=403,
            )

        return self.get_response(request)


class SenhaTemporariaMiddleware:
    """Obriga a troca da senha definida na criação/redefinição antes de
    acessar qualquer outra parte do sistema (superusuários não têm vínculo
    e nunca são afetados).

    Prazo de 7 dias (canis.senhas.PRAZO_TROCA_SENHA_DIAS): vencido o prazo
    sem troca, o acesso é bloqueado e o usuário cai na página de conta
    bloqueada, devendo falar com o desenvolvedor."""

    ROTAS_ISENTAS = (
        "/login/",
        "/logout/",
        "/trocar-senha/",
        "/conta-bloqueada/",
        "/static/",
        "/media/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.ROTAS_ISENTAS):
            return self.get_response(request)

        if request.user.is_authenticated:
            vinculo = getattr(request.user, "vinculo_canil", None)
            if vinculo is not None and vinculo.senha_temporaria:
                from .senhas import senha_temporaria_expirada

                if senha_temporaria_expirada(vinculo):
                    return redirect("conta_bloqueada")
                return redirect("trocar_senha_obrigatoria")

        return self.get_response(request)
