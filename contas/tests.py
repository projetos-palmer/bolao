from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class CadastroSemEmailTests(TestCase):
    def test_usuario_consegue_cadastrar_criar_senha_e_logar_sem_email(self):
        cpf = '529.982.247-25'
        senha = 'senha123'

        resposta = self.client.get(reverse('contas:cadastro'))
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, 'name="email"')

        resposta = self.client.post(reverse('contas:cadastro'), {
            'cpf': cpf,
            'nome_completo': 'Usuario Teste',
            'telefone': '(11) 99999-9999',
        })
        self.assertEqual(resposta.status_code, 302)

        usuario = Usuario.objects.get(cpf=cpf)
        self.assertIsNone(usuario.email)
        self.assertTrue(usuario.is_active)
        self.assertTrue(usuario.email_confirmado)

        resposta = self.client.post(resposta.url, {
            'senha': senha,
            'confirmar_senha': senha,
        })
        self.assertRedirects(resposta, reverse('contas:login'))

        resposta = self.client.post(reverse('contas:login'), {
            'cpf': cpf,
            'senha': senha,
        })
        self.assertRedirects(resposta, reverse('jogos:inicio'))
