from django.views.generic import UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse

from contas.models import Usuario
from .models import PixUsuario
from .forms import FormPixUsuario


class PerfilUsuarioView(LoginRequiredMixin, TemplateView):
    """Exibe o perfil do usuário logado."""
    template_name = 'usuarios/perfil.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pix'] = PixUsuario.objects.filter(usuario=self.request.user).first()
        return ctx


class PixUsuarioUpdateView(LoginRequiredMixin, UpdateView):
    """Cria ou atualiza os dados Pix do usuário."""
    model = PixUsuario
    form_class = FormPixUsuario
    template_name = 'usuarios/pix_form.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse_lazy('usuarios:perfil')

    def get_object(self, queryset=None):
        obj, _ = PixUsuario.objects.get_or_create(usuario=self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['next'] = self.request.GET.get('next', '')
        ctx['dominios_email'] = [
            '@gmail.com', '@hotmail.com', '@outlook.com', '@yahoo.com',
            '@icloud.com', '@live.com', '@msn.com', '@uol.com.br',
            '@bol.com.br', '@terra.com.br', '@ig.com.br', '@r7.com',
        ]
        return ctx

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, 'Dados Pix salvos com sucesso!')
        return super().form_valid(form)

