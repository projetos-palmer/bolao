from django import forms
from .models import Selecao, Jogo


class FormSelecao(forms.ModelForm):
    class Meta:
        model = Selecao
        fields = ['nome', 'sigla', 'bandeira', 'icone']


class FormJogo(forms.ModelForm):
    class Meta:
        model = Jogo
        fields = [
            'selecao_mandante', 'selecao_visitante',
            'data_hora', 'estadio', 'cidade',
            'fase', 'status',
            'placar_mandante', 'placar_visitante',
        ]
        widgets = {
            'data_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_hora'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean(self):
        dados = super().clean()
        mandante = dados.get('selecao_mandante')
        visitante = dados.get('selecao_visitante')
        if mandante and visitante and mandante == visitante:
            raise forms.ValidationError('A seleção mandante e visitante não podem ser a mesma.')
        return dados
