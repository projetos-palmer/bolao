from django.db.models import Sum
from django.views.generic import TemplateView, UpdateView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404

from boloes.models import Bolao, ParticipacaoBolao, Premio
from boloes.services import pagar_premios_bolao
from jogos.models import Jogo
from pagamentos.models import Pagamento, ConfiguracaoPixAdministrador, ConfiguracaoEmail
from contas.models import Usuario


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe acesso ao painel para staff."""
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'Acesso restrito. Você não tem permissão para acessar esta área.')
            return redirect('jogos:inicio')
        return redirect('contas:login')


class DashboardAdministradorView(AdminMixin, TemplateView):
    """Painel principal do administrador."""
    template_name = 'painel/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_usuarios'] = Usuario.objects.count()
        ctx['total_jogos'] = Jogo.objects.count()
        ctx['total_boloes'] = Bolao.objects.count()
        ctx['boloes_abertos'] = Bolao.objects.filter(status='aberto').count()
        pagamentos_qs = Pagamento.objects.filter(status='pendente').select_related(
            'participacao__usuario', 'participacao__bolao'
        )
        ctx['pagamentos_pendentes'] = pagamentos_qs.count()
        ctx['pagamentos_recentes'] = pagamentos_qs[:10]
        ctx['total_arrecadado'] = Pagamento.objects.filter(status='confirmado').aggregate(t=Sum('valor'))['t'] or 0
        ctx['total_pago_ganhadores'] = Premio.objects.filter(status_pagamento='pago').aggregate(t=Sum('valor'))['t'] or 0
        ctx['lucro_total'] = ctx['total_arrecadado'] - ctx['total_pago_ganhadores']
        ctx['boloes_recentes'] = Bolao.objects.select_related(
            'jogo__selecao_mandante', 'jogo__selecao_visitante'
        ).order_by('-id')[:5]
        ctx['boloes_em_premiacao'] = Bolao.objects.filter(
            status='premiacao'
        ).select_related('jogo__selecao_mandante', 'jogo__selecao_visitante').prefetch_related('premios')
        return ctx


class ConfiguracaoPixUpdateView(AdminMixin, UpdateView):
    """Atualiza a configuração Pix do administrador."""
    model = ConfiguracaoPixAdministrador
    fields = [
        'tipo_chave', 'chave_pix', 'nome_recebedor', 'banco', 'documento_recebedor', 'ativo',
        'client_id_efi', 'client_secret_efi', 'certificado_efi', 'ambiente_efi',
        'mp_access_token',
    ]
    template_name = 'painel/configuracao_pix.html'
    success_url = reverse_lazy('painel:dashboard')

    def get_object(self, queryset=None):
        obj, _ = ConfiguracaoPixAdministrador.objects.get_or_create(
            defaults={
                'tipo_chave': 'cpf',
                'chave_pix': '',
                'nome_recebedor': '',
                'banco': '',
                'documento_recebedor': '',
            }
        )
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Configuração Pix salva com sucesso!')
        return super().form_valid(form)


class ConfiguracaoEmailUpdateView(AdminMixin, UpdateView):
    """Atualiza a configuração de e-mail SMTP."""
    model = ConfiguracaoEmail
    fields = ['servidor_smtp', 'porta', 'usuario_email', 'senha_email', 'usar_tls', 'email_remetente', 'ativo']
    template_name = 'painel/configuracao_email.html'
    success_url = reverse_lazy('painel:dashboard')

    def get_object(self, queryset=None):
        obj, _ = ConfiguracaoEmail.objects.get_or_create(
            defaults={
                'servidor_smtp': 'smtp.gmail.com',
                'porta': 587,
                'usuario_email': '',
                'senha_email': '',
                'email_remetente': '',
            }
        )
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Configuração de e-mail salva com sucesso!')
        return super().form_valid(form)


class PagarPremiosBolaoView(AdminMixin, View):
    """
    Envia o prêmio PIX automaticamente para todos os ganhadores de um bolão.
    Requer credenciais EFI Bank configuradas.
    """

    def post(self, request, pk):
        bolao = get_object_or_404(Bolao, pk=pk)

        if bolao.status not in ('premiacao',):
            messages.error(request, 'Este bolão não está na etapa de premiação.')
            return redirect('painel:dashboard')

        try:
            resultado = pagar_premios_bolao(bolao)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('painel:dashboard')

        pagos = resultado['pagos']
        falhos = resultado['falhos']
        sem_pix = resultado['sem_pix']

        if pagos:
            nomes = ', '.join(p['usuario'] for p in pagos)
            messages.success(request, f'PIX enviado com sucesso para {len(pagos)} ganhador(es): {nomes}.')

        if sem_pix:
            nomes = ', '.join(p['usuario'] for p in sem_pix)
            messages.warning(request, f'{len(sem_pix)} ganhador(es) sem chave PIX cadastrada (pagamento manual necessário): {nomes}.')

        if falhos:
            nomes = ', '.join(f['usuario'] for f in falhos)
            messages.error(request, f'Falha ao enviar PIX para {len(falhos)} ganhador(es): {nomes}. Verifique os detalhes e tente novamente.')

        return redirect('painel:dashboard')

