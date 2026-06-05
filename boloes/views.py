from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models import Bolao, ParticipacaoBolao, Premio
from .forms import FormBolao, FormPalpite
from .services import calcular_ganhadores, verificar_boloes_para_fechar


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class BolaoListView(LoginRequiredMixin, ListView):
    model = Bolao
    template_name = 'boloes/bolao_list.html'
    context_object_name = 'boloes'

    def get_queryset(self):
        verificar_boloes_para_fechar()
        return Bolao.objects.filter(status='aberto').select_related('jogo__selecao_mandante', 'jogo__selecao_visitante')


class BolaoDetailView(LoginRequiredMixin, DetailView):
    model = Bolao
    template_name = 'boloes/bolao_detail.html'
    context_object_name = 'bolao'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['participacoes'] = self.object.participacoes.select_related('usuario').order_by('-data_palpite')
        ctx['ganhadores'] = Premio.objects.filter(bolao=self.object).select_related('usuario', 'participacao')
        return ctx


class BolaoCreateView(AdminMixin, CreateView):
    model = Bolao
    form_class = FormBolao
    template_name = 'boloes/bolao_form.html'
    success_url = reverse_lazy('boloes:bolao_list')

    def form_valid(self, form):
        messages.success(self.request, 'Bolão criado com sucesso!')
        return super().form_valid(form)


class BolaoUpdateView(AdminMixin, UpdateView):
    model = Bolao
    form_class = FormBolao
    template_name = 'boloes/bolao_form.html'
    success_url = reverse_lazy('boloes:bolao_list')

    def form_valid(self, form):
        messages.success(self.request, 'Bolão atualizado!')
        return super().form_valid(form)


class ParticiparBolaoView(LoginRequiredMixin, DetailView):
    """Exibe o bolão e processa o palpite do usuário."""
    model = Bolao
    template_name = 'boloes/participar.html'
    context_object_name = 'bolao'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from usuarios.models import PixUsuario
            tem_pix = PixUsuario.objects.filter(usuario=request.user, chave_pix__gt='').exists()
            if not tem_pix:
                messages.warning(request, 'Você precisa cadastrar sua chave Pix antes de fazer uma aposta. O prêmio será enviado para ela!')
                return redirect(f"{reverse('usuarios:pix')}?next={request.get_full_path()}")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = FormPalpite()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        bolao = self.object

        if not bolao.jogo.esta_aberto_para_apostas:
            messages.error(request, 'Este bolão foi encerrado para novas apostas. O prazo limite era 5 minutos antes do início da partida.')
            return redirect('boloes:bolao_detail', pk=bolao.pk)

        form = FormPalpite(request.POST)
        if form.is_valid():
            participacao = form.save(commit=False)
            participacao.usuario = request.user
            participacao.bolao = bolao
            participacao.bloqueado_para_edicao = True
            participacao.save()
            messages.success(request, 'Palpite salvo com sucesso. Selecione este e outros jogos em aberto para pagar com Pix.')
            return redirect('boloes:meus_jogos')

        return self.render_to_response(self.get_context_data(form=form))


class MeusJogosListView(LoginRequiredMixin, ListView):
    """Lista todas as participações do usuário logado."""
    template_name = 'boloes/meus_jogos.html'
    context_object_name = 'participacoes'

    FILTROS_VALIDOS = {
        'aguardando': 'aguardando',
        'confirmado': 'confirmado',
        'expirado': 'expirado',
    }

    def get_queryset(self):
        from django.db.models import F
        qs = ParticipacaoBolao.objects.filter(
            usuario=self.request.user
        ).select_related('bolao__jogo__selecao_mandante', 'bolao__jogo__selecao_visitante').order_by('-data_palpite')

        filtro_status = self.request.GET.get('status')
        if filtro_status in self.FILTROS_VALIDOS:
            qs = qs.filter(status=filtro_status)

        filtro_jogo = self.request.GET.get('jogo')
        if filtro_jogo:
            qs = qs.filter(bolao__jogo__pk=filtro_jogo)

        if self.request.GET.get('acertou') == '1':
            qs = qs.filter(
                bolao__jogo__placar_mandante=F('placar_mandante'),
                bolao__jogo__placar_visitante=F('placar_visitante'),
                bolao__jogo__placar_mandante__isnull=False,
            )

        return qs

    def get_context_data(self, **kwargs):
        from jogos.models import Jogo
        ctx = super().get_context_data(**kwargs)
        ctx['filtro_status'] = self.request.GET.get('status', '')
        ctx['filtro_jogo'] = self.request.GET.get('jogo', '')
        ctx['filtro_acertou'] = self.request.GET.get('acertou', '')
        # jogos em que o usuário tem pelo menos uma participação
        ctx['jogos_disponiveis'] = (
            Jogo.objects
            .filter(boloes__participacoes__usuario=self.request.user)
            .select_related('selecao_mandante', 'selecao_visitante')
            .distinct()
            .order_by('-data_hora')
        )
        return ctx


class ResultadoBolaoView(LoginRequiredMixin, DetailView):
    """Exibe resultado de um bolão com ganhadores e todos os participantes."""
    model = Bolao
    template_name = 'boloes/resultado.html'
    context_object_name = 'bolao'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['ganhadores'] = Premio.objects.filter(bolao=self.object).select_related('usuario', 'participacao')
        ctx['participacoes'] = self.object.participacoes.select_related(
            'usuario'
        ).prefetch_related('pagamento').order_by('-data_palpite')
        return ctx


class GerarGanhadoresView(AdminMixin, DetailView):
    """Calcula e gera os ganhadores do bolão (apenas admin)."""
    model = Bolao

    def post(self, request, *args, **kwargs):
        bolao = self.get_object()
        jogo = bolao.jogo
        if not jogo.resultado_definido:
            messages.error(request, 'Informe o placar do jogo antes de gerar os ganhadores.')
            return redirect('boloes:bolao_detail', pk=bolao.pk)
        premios = calcular_ganhadores(bolao)
        if premios:
            messages.success(request, f'{len(premios)} ganhador(es) encontrado(s)! Prêmios calculados.')
        else:
            messages.warning(request, 'Nenhum acertador neste bolão. Prêmio tratado conforme a regra configurada.')
        return redirect('boloes:resultado', pk=bolao.pk)

