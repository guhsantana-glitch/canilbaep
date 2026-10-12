from django.contrib import admin
from django.http import Http404
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.static import serve as media_serve
import posixpath

urlpatterns = [
    path("admin/", admin.site.urls),
    path("gestao/", include("gestaocanis.urls")),
    path("racoes/", include("racoes.urls")),
    path("", include("core.urls")),
]


@login_required
def media_protegida(request, path):
    """Serve arquivos de MEDIA_ROOT apenas para usuários autenticados.

    Funciona em produção (DEBUG=False), onde o helper `static()` do Django
    não atua — sem isso, fotos e documentos retornam 404 na nuvem.
    """
    normalizado = posixpath.normpath("/" + path).lstrip("/")
    if not normalizado or normalizado.startswith((".", "/")) or ".." in normalizado.split("/"):
        raise Http404()
    return media_serve(request, normalizado, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", media_protegida),
]
