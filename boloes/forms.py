from django import forms
from django.utils import timezone

from jogos.models import Jogo
from .models import Bolao, ParticipacaoBolao


class FormBolao(forms.ModelForm):
    class Meta:
        model = Bolao
        fields = [
            'jogo', 'nome', 'valor_participacao',
            'percentual_premiacao', 'status',
            'data_abertura', 'data_fechamento',
            'regra_sem_ganhador',
        ]
        widgets = {
            'data_abertura': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'data_fechamento': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_abertura'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['data_fechamento'].input_formats = ['%Y-%m-%dT%H:%M']
        # Ao criar (sem instância), só mostra jogos futuros; ao editar mantém o jogo atual
        agora = timezone.now()
        qs = Jogo.objects.filter(data_hora__gt=agora).select_related('selecao_mandante', 'selecao_visitante').order_by('data_hora')
        if self.instance and self.instance.pk and self.instance.jogo_id:
            # inclui o jogo já salvo para não sumir no formulário de edição
            qs = (qs | Jogo.objects.filter(pk=self.instance.jogo_id)).distinct().order_by('data_hora')
        self.fields['jogo'].queryset = qs

    def clean_percentual_premiacao(self):
        perc = self.cleaned_data.get('percentual_premiacao', 0)
        if not (0 <= perc <= 100):
            raise forms.ValidationError('O percentual deve ser entre 0 e 100.')
        return perc


class FormPalpite(forms.ModelForm):
    """Formulário de palpite para participação no bolão."""
    confirmacao = forms.BooleanField(
        label='Entendo que este palpite não poderá ser alterado após salvo.',
        required=True,
    )

    class Meta:
        model = ParticipacaoBolao
        fields = ['placar_mandante', 'placar_visitante']
        widgets = {
            'placar_mandante': forms.NumberInput(attrs={'min': 0, 'max': 99, 'class': 'placar-input'}),
            'placar_visitante': forms.NumberInput(attrs={'min': 0, 'max': 99, 'class': 'placar-input'}),
        }
