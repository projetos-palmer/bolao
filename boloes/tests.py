from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Usuario
from jogos.models import Jogo, Selecao
from usuarios.models import PixUsuario

from .models import Bolao, ParticipacaoBolao


class ParticiparBolaoTests(TestCase):
    def test_apos_palpite_redireciona_para_meus_jogos(self):
        usuario = Usuario.objects.create_user(
            cpf='529.982.247-25',
            nome_completo='Usuario Teste',
            telefone='(11) 99999-9999',
            password='senha123',
        )
        usuario.is_active = True
        usuario.email_confirmado = True
        usuario.save(update_fields=['is_active', 'email_confirmado'])
        PixUsuario.objects.create(
            usuario=usuario,
            tipo_chave='cpf',
            chave_pix='529.982.247-25',
            nome_recebedor='Usuario Teste',
            banco='Banco Teste',
        )

        mandante = Selecao.objects.create(nome='Brasil', sigla='BRA', icone='🇧🇷')
        visitante = Selecao.objects.create(nome='Argentina', sigla='ARG', icone='🇦🇷')
        jogo = Jogo.objects.create(
            selecao_mandante=mandante,
            selecao_visitante=visitante,
            data_hora=timezone.now() + timedelta(days=1),
            status='aberto',
        )
        bolao = Bolao.objects.create(
            jogo=jogo,
            nome='Bolão Teste',
            valor_participacao='10.00',
            percentual_premiacao=70,
            status='aberto',
        )

        self.client.force_login(usuario)
        resposta = self.client.post(reverse('boloes:participar', args=[bolao.pk]), {
            'placar_mandante': 2,
            'placar_visitante': 1,
            'confirmacao': 'on',
        })

        self.assertRedirects(resposta, reverse('boloes:meus_jogos'))
        self.assertTrue(
            ParticipacaoBolao.objects.filter(
                usuario=usuario,
                bolao=bolao,
                status='aguardando',
            ).exists()
        )
