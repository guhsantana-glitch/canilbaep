from django import forms
from .models import (
    Cao, Condutor, Vacina, Medicamento, Pesagem, Treinamento, Documento,
    Veterinario, TipoVacina, Vermifugacao, Ectoparasita, OcorrenciaSaude,
    VisitaTecnica,
)

ISO_DATE = "%Y-%m-%d"


class DataISOField(forms.DateField):
    """Campo de data que aceita e exibe corretamente o formato usado pelo
    <input type="date"> do navegador (AAAA-MM-DD), independente do locale."""
    input_formats = [ISO_DATE, "%d/%m/%Y"]
    widget = forms.DateInput(attrs={"type": "date"}, format=ISO_DATE)


class CaoForm(forms.ModelForm):
    data_nascimento = DataISOField(label="Data de nascimento", required=False)
    data_ingresso = DataISOField(label="Data de ingresso no plantel")

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["condutor_atual"].queryset = (
                Condutor.objects.filter(canil=canil).order_by("nome")
            )

    class Meta:
        model = Cao
        fields = [
            "nome", "raca", "sexo", "microchip", "data_nascimento", "data_ingresso",
            "status", "condutor_atual", "box", "foto", "origem",
            "especialidade", "numero_cro_cpr", "registro_sbcpa", "patrimonio", "observacoes",
        ]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}


class CondutorForm(forms.ModelForm):
    class Meta:
        model = Condutor
        fields = ["nome", "matricula", "posto_graduacao", "telefone", "ativo", "observacoes"]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}


class VeterinarioForm(forms.ModelForm):
    class Meta:
        model = Veterinario
        fields = ["nome", "crmv", "telefone", "email", "ativo", "observacoes"]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}


class TipoVacinaForm(forms.ModelForm):
    data_fabricacao = DataISOField(label="Data de fabricação", required=False)
    data_validade = DataISOField(label="Data de validade", required=False)

    class Meta:
        model = TipoVacina
        fields = ["nome", "nome_comercial", "fabricante", "partida",
                  "data_fabricacao", "data_validade", "descricao", "ativo"]


class VacinaForm(forms.ModelForm):
    data_aplicacao = DataISOField(label="Data da vacinação")
    data_proxima_dose = DataISOField(label="Revacinar em", required=False)

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["tipo"].queryset = TipoVacina.objects.filter(canil=canil).order_by("nome")
            self.fields["veterinario"].queryset = Veterinario.objects.filter(canil=canil).order_by("nome")

    class Meta:
        model = Vacina
        fields = ["tipo", "data_aplicacao", "data_proxima_dose", "veterinario", "lote", "observacoes"]


class MedicamentoForm(forms.ModelForm):
    data_inicio = DataISOField(label="Início do tratamento")
    data_fim = DataISOField(label="Fim do tratamento", required=False)

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["veterinario"].queryset = Veterinario.objects.filter(canil=canil).order_by("nome")

    class Meta:
        model = Medicamento
        fields = ["nome", "dosagem", "motivo", "data_inicio", "data_fim", "veterinario", "observacoes"]


class PesagemForm(forms.ModelForm):
    data = DataISOField(label="Data")

    class Meta:
        model = Pesagem
        fields = ["data", "peso_kg", "observacoes"]


class TreinamentoForm(forms.ModelForm):
    data = DataISOField(label="Data")

    class Meta:
        model = Treinamento
        fields = ["data", "etapa", "descricao", "resultado", "nota_avaliacao", "instrutor"]


class DocumentoForm(forms.ModelForm):
    data_documento = DataISOField(label="Data do documento", required=False)

    class Meta:
        model = Documento
        fields = ["tipo", "titulo", "arquivo", "data_documento"]


class VermifugacaoForm(forms.ModelForm):
    data_aplicacao = DataISOField(label="Data de aplicação")

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["veterinario"].queryset = Veterinario.objects.filter(canil=canil).order_by("nome")

    class Meta:
        model = Vermifugacao
        fields = ["vermifugo", "data_aplicacao", "veterinario", "lote", "observacoes"]


class EctoparasitaForm(forms.ModelForm):
    data_aplicacao = DataISOField(label="Aplicação em")

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["veterinario"].queryset = Veterinario.objects.filter(canil=canil).order_by("nome")

    class Meta:
        model = Ectoparasita
        fields = ["procedimento", "data_aplicacao", "veterinario", "observacoes"]


class OcorrenciaSaudeForm(forms.ModelForm):
    data = DataISOField(label="Data")

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["veterinario"].queryset = Veterinario.objects.filter(canil=canil).order_by("nome")

    class Meta:
        model = OcorrenciaSaude
        fields = ["anormalidade", "data", "veterinario", "medicamento", "observacoes"]


class VisitaTecnicaForm(forms.ModelForm):
    data = DataISOField(label="Data da visita")

    class Meta:
        model = VisitaTecnica
        fields = ["data", "medico_veterinario", "observacoes"]


class RelatorioMensalForm(forms.Form):
    cao = forms.ModelChoiceField(queryset=Cao.objects.all(), label="Cão")
    data_inicio = DataISOField(label="De")
    data_fim = DataISOField(label="Até")

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["cao"].queryset = Cao.objects.filter(canil=canil).order_by("nome")


class RelatorioGeralForm(forms.Form):
    data_inicio = DataISOField(label="De")
    data_fim = DataISOField(label="Até")
    apenas_ativos = forms.BooleanField(label="Somente cães ativos no plantel", required=False, initial=True)
