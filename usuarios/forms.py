import re
from django import forms
from validate_docbr import CPF
from .models import PixUsuario

cpf_validator = CPF()


def formatar_cpf(valor):
    """Remove não-dígitos e formata como 000.000.000-00."""
    digits = re.sub(r'\D', '', valor)
    if len(digits) == 11:
        return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'
    return valor


def formatar_telefone(valor):
    """Remove não-dígitos e formata como (00)00000-0000."""
    digits = re.sub(r'\D', '', valor)
    if len(digits) == 11:
        return f'({digits[:2]}){digits[2:7]}-{digits[7:]}'
    if len(digits) == 10:
        return f'({digits[:2]}){digits[2:6]}-{digits[6:]}'
    return valor


class FormPixUsuario(forms.ModelForm):
    """Formulário para cadastro/edição do Pix do usuário."""

    class Meta:
        model = PixUsuario
        fields = ['tipo_chave', 'chave_pix', 'nome_recebedor', 'banco']

    def clean(self):
        dados = super().clean()
        tipo = dados.get('tipo_chave')
        chave = dados.get('chave_pix', '').strip()

        if tipo == 'cpf':
            chave_formatada = formatar_cpf(chave)
            dados['chave_pix'] = chave_formatada
            if not cpf_validator.validate(chave_formatada):
                self.add_error('chave_pix', 'CPF inválido. Verifique os números digitados.')
        elif tipo == 'telefone':
            chave_formatada = formatar_telefone(chave)
            dados['chave_pix'] = chave_formatada
            padrao = re.compile(r'^\(\d{2}\)\d{4,5}-\d{4}$')
            if not padrao.match(chave_formatada):
                self.add_error('chave_pix', 'Telefone inválido. Use o formato (00)00000-0000.')
        elif tipo == 'email':
            if '@' not in chave or '.' not in chave.split('@')[-1]:
                self.add_error('chave_pix', 'E-mail inválido.')

        return dados
