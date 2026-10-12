from django import forms
from canis.models import Canil, Unidade


class UnidadeForm(forms.ModelForm):
    class Meta:
        model = Unidade
        fields = ["nome", "cidade_sede", "comandante", "telefone",
                  "email", "ativo", "observacoes"]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}


class CanilForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidade"].queryset = Unidade.objects.filter(ativo=True).order_by("nome")

    class Meta:
        model = Canil
        fields = ["unidade", "nome", "cidade", "responsavel", "telefone",
                  "email", "ativo", "observacoes"]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}
