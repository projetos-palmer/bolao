import re
from django import forms
from validate_docbr import CPF
from .models import Usuario

cpf_validator = CPF()


class FormCadastroUsuario(forms.ModelForm):
    """Formulário de cadastro de usuário."""

    class Meta:
        model = Usuario
        fields = ['cpf', 'nome_completo', 'telefone']
        widgets = {
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'maxlength': '14'}),
            'nome_completo': forms.TextInput(attrs={'placeholder': 'Seu nome completo'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(00) 99999-9999', 'maxlength': '15'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        if not cpf_validator.validate(cpf):
            raise forms.ValidationError('CPF inválido. Informe um CPF válido no formato 000.000.000-00.')
        qs = Usuario.objects.filter(cpf=cpf)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Este CPF já está cadastrado.')
        return cpf

    def clean_nome_completo(self):
        nome = self.cleaned_data.get('nome_completo', '').strip()
        partes = nome.split()
        if len(partes) < 2:
            raise forms.ValidationError('Informe o nome completo (mínimo duas palavras).')
        return nome

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '')
        padrao = re.compile(r'^\(\d{2}\)\s?\d{4,5}-\d{4}$')
        if not padrao.match(telefone):
            raise forms.ValidationError('Telefone inválido. Use o formato (00) 99999-9999.')
        qs = Usuario.objects.filter(telefone=telefone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Este telefone já está cadastrado.')
        return telefone

class FormCriarSenha(forms.Form):
    """Formulário para criação de senha após cadastro."""
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Crie uma senha com mais de 4 caracteres'}),
        min_length=5,
        error_messages={'min_length': 'A senha deve ter mais de 4 caracteres.'},
    )
    confirmar_senha = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repita a senha'}),
    )

    def clean(self):
        dados = super().clean()
        senha = dados.get('senha')
        confirmar = dados.get('confirmar_senha')
        if senha and confirmar and senha != confirmar:
            raise forms.ValidationError('As senhas não coincidem.')
        return dados

class FormLoginUsuario(forms.Form):
    """Formulario de login exclusivamente por CPF."""
    cpf = forms.CharField(
        label='CPF',
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite seu CPF: 000.000.000-00',
            'maxlength': '14',
            'autocomplete': 'username',
        }),
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Sua senha', 'autocomplete': 'current-password'}),
    )

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '').strip()
        numeros = re.sub(r'\D', '', cpf)
        if len(numeros) == 11:
            cpf = f'{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}'
        if not cpf_validator.validate(cpf):
            raise forms.ValidationError('CPF inválido. Informe o CPF usado no cadastro.')
        return cpf
