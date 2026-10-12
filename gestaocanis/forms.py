from django import forms
from canis.models import Canil


class CanilForm(forms.ModelForm):
    class Meta:
        model = Canil
        fields = ["nome", "unidade", "cidade", "responsavel", "telefone",
                  "email", "ativo", "observacoes"]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}
