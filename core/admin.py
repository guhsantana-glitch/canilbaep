from django.contrib import admin
from .models import Condutor, Cao, Vacina, Medicamento, Pesagem, Treinamento, Documento, Veterinario, TipoVacina


class VacinaInline(admin.TabularInline):
    model = Vacina
    extra = 0


class MedicamentoInline(admin.TabularInline):
    model = Medicamento
    extra = 0


class PesagemInline(admin.TabularInline):
    model = Pesagem
    extra = 0


class TreinamentoInline(admin.TabularInline):
    model = Treinamento
    extra = 0


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0


@admin.register(Cao)
class CaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "raca", "sexo", "status", "condutor_atual", "box", "data_ingresso")
    list_filter = ("status", "sexo", "raca")
    search_fields = ("nome", "microchip", "box")
    inlines = [PesagemInline, VacinaInline, MedicamentoInline, TreinamentoInline, DocumentoInline]


@admin.register(Condutor)
class CondutorAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "posto_graduacao", "ativo", "telefone")
    search_fields = ("nome", "matricula")
    list_filter = ("ativo",)


@admin.register(Vacina)
class VacinaAdmin(admin.ModelAdmin):
    list_display = ("cao", "tipo", "data_aplicacao", "data_proxima_dose")
    list_filter = ("tipo",)
    search_fields = ("cao__nome", "tipo")


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ("cao", "nome", "data_inicio", "data_fim")
    search_fields = ("cao__nome", "nome")


@admin.register(Pesagem)
class PesagemAdmin(admin.ModelAdmin):
    list_display = ("cao", "data", "peso_kg")
    list_filter = ("cao",)


@admin.register(Treinamento)
class TreinamentoAdmin(admin.ModelAdmin):
    list_display = ("cao", "etapa", "data", "instrutor")
    list_filter = ("etapa",)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("cao", "tipo", "titulo", "enviado_em")
    list_filter = ("tipo",)


@admin.register(Veterinario)
class VeterinarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "crmv", "telefone", "ativo")
    search_fields = ("nome", "crmv")
    list_filter = ("ativo",)


@admin.register(TipoVacina)
class TipoVacinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao", "ativo")
    list_filter = ("ativo",)
