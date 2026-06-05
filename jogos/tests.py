from django.test import TestCase
from django.urls import reverse

from .models import Selecao, VotoCampeao


class EnqueteCampeaoTests(TestCase):
    def setUp(self):
        self.brasil = Selecao.objects.create(nome='Brasil', sigla='BRA', icone='🇧🇷')
        self.argentina = Selecao.objects.create(nome='Argentina', sigla='ARG', icone='🇦🇷')

    def test_enquete_aparece_na_pagina_inicial(self):
        resposta = self.client.get(reverse('jogos:inicio'))

        self.assertContains(resposta, 'Enquete: Qual seleção será a campeã do mundo?')
        self.assertContains(resposta, 'Brasil')
        self.assertContains(resposta, 'Argentina')

    def test_visitante_vota_sem_login(self):
        resposta = self.client.post(
            reverse('jogos:votar_campeao'),
            {'selecao': self.brasil.pk},
            follow=True,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(VotoCampeao.objects.count(), 1)
        self.assertEqual(VotoCampeao.objects.get().selecao, self.brasil)
        self.assertContains(resposta, 'Voto confirmado!')

    def test_voto_da_mesma_sessao_atualiza_a_selecao(self):
        self.client.post(reverse('jogos:votar_campeao'), {'selecao': self.brasil.pk})
        self.client.post(reverse('jogos:votar_campeao'), {'selecao': self.argentina.pk})

        self.assertEqual(VotoCampeao.objects.count(), 1)
        self.assertEqual(VotoCampeao.objects.get().selecao, self.argentina)

    def test_ranking_mostra_apenas_tres_mais_votadas(self):
        franca = Selecao.objects.create(nome='França', sigla='FRA', icone='🇫🇷')
        espanha = Selecao.objects.create(nome='Espanha', sigla='ESP', icone='🇪🇸')

        for session_key, selecao in [
            ('sessao-1', self.brasil),
            ('sessao-2', self.brasil),
            ('sessao-3', self.argentina),
            ('sessao-4', franca),
            ('sessao-5', espanha),
        ]:
            VotoCampeao.objects.create(session_key=session_key, selecao=selecao)

        resposta = self.client.get(reverse('jogos:inicio'))
        mais_votadas = list(resposta.context['selecoes_mais_votadas'])

        self.assertEqual(len(mais_votadas), 3)
        self.assertEqual(mais_votadas[0], self.brasil)
        self.assertEqual(mais_votadas[0].total_votos, 2)
        self.assertEqual(mais_votadas[0].percentual_barra, '40.0')
