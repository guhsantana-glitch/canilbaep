from django import forms
from core.forms import DataISOField
from .models import Racao, MovimentacaoRacao


class RacaoForm(forms.ModelForm):
    class Meta:
        model = Racao
        fields = ["nome", "marca", "descricao", "estoque_minimo_kg", "ativo"]


class EntradaRacaoForm(forms.ModelForm):
    data = DataISOField(label="Data da entrada")

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["racao"].queryset = Racao.objects.filter(canil=canil, ativo=True).order_by("nome")

    class Meta:
        model = MovimentacaoRacao
        fields = ["racao", "data", "quantidade_kg", "motivo"]


class SaidaRacaoForm(forms.ModelForm):
    data = DataISOField(label="Data da saída")

    def __init__(self, *args, canil=None, **kwargs):
        super().__init__(*args, **kwargs)
        if canil is not None:
            self.fields["racao"].queryset = Racao.objects.filter(canil=canil, ativo=True).order_by("nome")

    class Meta:
        model = MovimentacaoRacao
        fields = ["racao", "data", "quantidade_kg", "motivo"]
