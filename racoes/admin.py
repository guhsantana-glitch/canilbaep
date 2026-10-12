from django.contrib import admin
from .models import Racao, MovimentacaoRacao


@admin.register(Racao)
class RacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "marca", "canil", "ativo")
    list_filter = ("ativo", "canil")
    search_fields = ("nome", "marca")


@admin.register(MovimentacaoRacao)
class MovimentacaoRacaoAdmin(admin.ModelAdmin):
    list_display = ("racao", "tipo", "data", "quantidade_kg", "responsavel")
    list_filter = ("tipo",)
