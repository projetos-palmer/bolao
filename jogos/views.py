from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Count, Prefetch
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from boloes.models import Bolao
from .models import Jogo, Selecao, VotoCampeao
from .forms import FormJogo, FormSelecao


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin que restringe acesso apenas a administradores (staff)."""
    def test_func(self):
        return self.request.user.is_staff


def jogo_data_hora_json(request, pk):
    """Retorna data_hora e limite_aposta do jogo em formato JSON (uso interno do form de bolão)."""
    if not request.user.is_staff:
        from django.http import Http404
        raise Http404
    jogo = get_object_or_404(Jogo, pk=pk)
    limite = jogo.data_hora - timedelta(minutes=5)
    # Formato 'YYYY-MM-DDTHH:MM' para input datetime-local
    fmt = '%Y-%m-%dT%H:%M'
    return JsonResponse({
        'data_hora': jogo.data_hora.strftime(fmt),
        'limite_aposta': limite.strftime(fmt),
    })


class PaginaInicialView(TemplateView):
    """Página inicial pública com jogos em destaque."""
    template_name = 'jogos/pagina_inicial.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        boloes_abertos = Bolao.objects.filter(status='aberto').order_by('valor_participacao')
        ctx['jogos'] = (
            Jogo.objects
            .filter(status='aberto')
            .select_related('selecao_mandante', 'selecao_visitante')
            .prefetch_related(Prefetch('boloes', queryset=boloes_abertos, to_attr='boloes_abertos'))
            .order_by('data_hora')[:10]
        )
        total_votos = VotoCampeao.objects.count()
        selecoes_mais_votadas = (
            Selecao.objects
            .annotate(total_votos=Count('votos_campeao'))
            .filter(total_votos__gt=0)
            .order_by('-total_votos', 'nome')[:3]
        )
        for selecao in selecoes_mais_votadas:
            selecao.percentual_votos = (selecao.total_votos / total_votos * 100) if total_votos else 0
            selecao.percentual_barra = f'{selecao.percentual_votos:.1f}'
        ctx['selecoes'] = Selecao.objects.all()
        ctx['total_votos_enquete'] = total_votos
        ctx['selecoes_mais_votadas'] = selecoes_mais_votadas
        ctx['voto_campeao_selecao_id'] = (
            VotoCampeao.objects
            .filter(session_key=self.request.session.session_key)
            .values_list('selecao_id', flat=True)
            .first()
        )
        return ctx


def votar_campeao(request):
    if request.method != 'POST':
        return redirect('jogos:inicio')

    selecao = get_object_or_404(Selecao, pk=request.POST.get('selecao'))
    if not request.session.session_key:
        request.session.create()

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    VotoCampeao.objects.update_or_create(
        session_key=request.session.session_key,
        defaults={
            'selecao': selecao,
            'ip': ip or None,
            'user_agent': user_agent,
        },
    )
    messages.success(request, f'Voto confirmado! Sua torcida por {selecao.nome} entrou em campo.')
    return redirect(f'{reverse_lazy("jogos:inicio")}#enquete-campeao')


class JogoListView(LoginRequiredMixin, ListView):
    model = Jogo
    template_name = 'jogos/jogo_list.html'
    context_object_name = 'jogos'
    queryset = Jogo.objects.select_related('selecao_mandante', 'selecao_visitante').order_by('data_hora')


class JogoDetailView(LoginRequiredMixin, DetailView):
    model = Jogo
    template_name = 'jogos/jogo_detail.html'
    context_object_name = 'jogo'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['boloes'] = self.object.boloes.filter(status='aberto')
        return ctx


class JogoCreateView(AdminMixin, CreateView):
    model = Jogo
    form_class = FormJogo
    template_name = 'jogos/jogo_form.html'
    success_url = reverse_lazy('jogos:jogo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jogo cadastrado com sucesso!')
        return super().form_valid(form)


class JogoUpdateView(AdminMixin, UpdateView):
    model = Jogo
    form_class = FormJogo
    template_name = 'jogos/jogo_form.html'
    success_url = reverse_lazy('jogos:jogo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jogo atualizado com sucesso!')
        return super().form_valid(form)


class JogoDeleteView(AdminMixin, DeleteView):
    model = Jogo
    template_name = 'jogos/jogo_confirm_delete.html'
    success_url = reverse_lazy('jogos:jogo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jogo removido.')
        return super().form_valid(form)

