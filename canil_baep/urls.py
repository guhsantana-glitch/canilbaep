from django.contrib import admin
from django.http import Http404
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.static import serve as media_serve
from django.db.models import Q
import posixpath

from canis.utils import canil_atual
from core.models import Cao, Documento


class AdminCanilSite(admin.AdminSite):
    """Admin do Django restrito a superusuários.

    Qualquer conta com is_staff veria e editaria TODOS os dados de TODOS os
    canis (não há escopo por tenant no admin padrão). Como hoje só o gestor
    geral usa o /admin/, o acesso é liberado apenas para superusuário.
    """

    def has_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)


admin_site = AdminCanilSite(name="admin")

urlpatterns = [
    path("admin/", admin_site.urls),
    path("gestao/", include("gestaocanis.urls")),
    path("racoes/", include("racoes.urls")),
    path("", include("core.urls")),
]


def _q_pelotao(request):
    """Escopo de pelotão para arquivos de mídia (mesma regra das listas)."""
    if request.user.is_superuser:
        return Q()
    vinculo = getattr(request.user, "vinculo_canil", None)
    if vinculo is None or vinculo.papel == "admin_canil":
        return Q()
    if vinculo.pelotao_id is None:
        return Q(pk__in=[])
    return Q(pelotao_id=vinculo.pelotao_id)


def _autorizado(request, caminho):
    """Confere se o usuário pode acessar aquele arquivo.

    Sem essa checagem, qualquer usuário logado quebia um link de /media/
    baixaria laudos e fotos de cães de OUTROS canis.
    """
    if request.user.is_superuser and canil_atual(request) is None:
        return True  # gestor geral sem canil selecionado
    canil = canil_atual(request)
    if canil is None:
        return False
    escopo = _q_pelotao(request)
    if caminho.startswith("caes/fotos/"):
        return Cao.objects.filter(escopo, canil=canil, foto=caminho).exists()
    if caminho.startswith("caes/documentos/"):
        return Documento.objects.filter(cao__canil=canil).filter(
            _q_documento_pelotao(request)
        ).filter(arquivo=caminho).exists()
    return False


def _q_documento_pelotao(request):
    if request.user.is_superuser:
        return Q()
    vinculo = getattr(request.user, "vinculo_canil", None)
    if vinculo is None or vinculo.papel == "admin_canil":
        return Q()
    if vinculo.pelotao_id is None:
        return Q(cao__pk__in=[])
    return Q(cao__pelotao_id=vinculo.pelotao_id)


@login_required
def media_protegida(request, path):
    """Serve arquivos de MEDIA_ROOT apenas a quem pode vê-los.

    Funciona em produção (DEBUG=False), onde o helper `static()` do Django
    não atua — sem isso, fotos e documentos retornam 404 na nuvem.
    """
    normalizado = posixpath.normpath("/" + path).lstrip("/")
    if not normalizado or normalizado.startswith((".", "/")) or ".." in normalizado.split("/"):
        raise Http404()
    if not _autorizado(request, normalizado):
        raise Http404()
    return media_serve(request, normalizado, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", media_protegida),
]