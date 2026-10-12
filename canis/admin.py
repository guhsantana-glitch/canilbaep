from django.contrib import admin
from .models import Canil, Unidade, VinculoUsuario


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "cidade_sede", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "cidade_sede")


@admin.register(Canil)
class CanilAdmin(admin.ModelAdmin):
    list_display = ("nome", "unidade", "cidade", "ativo", "criado_em")
    list_filter = ("ativo", "unidade")
    search_fields = ("nome", "cidade")


@admin.register(VinculoUsuario)
class VinculoUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "canil", "papel", "ativo")
    list_filter = ("papel", "ativo", "canil")
