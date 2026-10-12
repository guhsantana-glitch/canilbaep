from django.contrib import admin
from .models import Canil, VinculoUsuario


@admin.register(Canil)
class CanilAdmin(admin.ModelAdmin):
    list_display = ("nome", "unidade", "cidade", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "unidade", "cidade")


@admin.register(VinculoUsuario)
class VinculoUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "canil", "papel", "ativo")
    list_filter = ("papel", "ativo", "canil")
