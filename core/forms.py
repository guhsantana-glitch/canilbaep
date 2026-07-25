from django import forms
from .models import Cao, Condutor, Vacina, Medicamento, Pesagem, Treinamento, Documento


class CaoForm(forms.ModelForm):
    class Meta:
        model = Cao
        fields = [
            "nome", "raca", "sexo", "microchip", "data_nascimento", "data_ingresso",
            "status", "condutor_atual", "box", "foto", "origem", "observacoes",
        ]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "data_ingresso": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class CondutorForm(forms.ModelForm):
    class Meta:
        model = Condutor
        fields = ["nome", "matricula", "posto_graduacao", "telefone", "ativo", "observacoes"]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}


class VacinaForm(forms.ModelForm):
    class Meta:
        model = Vacina
        fields = ["tipo", "data_aplicacao", "data_proxima_dose", "veterinario", "lote", "observacoes"]
        widgets = {
            "data_aplicacao": forms.DateInput(attrs={"type": "date"}),
            "data_proxima_dose": forms.DateInput(attrs={"type": "date"}),
        }


class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ["nome", "dosagem", "motivo", "data_inicio", "data_fim", "veterinario", "observacoes"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
        }


class PesagemForm(forms.ModelForm):
    class Meta:
        model = Pesagem
        fields = ["data", "peso_kg", "observacoes"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}


class TreinamentoForm(forms.ModelForm):
    class Meta:
        model = Treinamento
        fields = ["data", "etapa", "descricao", "resultado", "instrutor"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ["tipo", "titulo", "arquivo", "data_documento"]
        widgets = {"data_documento": forms.DateInput(attrs={"type": "date"})}


class RelatorioMensalForm(forms.Form):
    cao = forms.ModelChoiceField(queryset=Cao.objects.all(), label="Cão")
    data_inicio = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="De")
    data_fim = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Até")
