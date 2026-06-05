from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Prefetch
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from boloes.models import Bolao
from .models import Jogo, Selecao
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
        return ctx


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

