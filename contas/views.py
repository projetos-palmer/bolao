from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from .models import Usuario
from .forms import FormCadastroUsuario, FormCriarSenha, FormLoginUsuario
from .tokens import token_confirmacao


class CadastroUsuarioView(View):
    """Cadastro de novo usuário — redireciona direto para criação de senha."""

    template_name = 'contas/cadastro.html'

    def get(self, request):
        form = FormCadastroUsuario()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = FormCadastroUsuario(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = True
            usuario.email_confirmado = True
            usuario.save()
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = token_confirmacao.make_token(usuario)
            messages.success(request, 'Cadastro realizado! Agora crie sua senha.')
            return redirect('contas:criar_senha', uidb64=uid, token=token)
        return render(request, self.template_name, {'form': form})


class ConfirmarEmailView(View):
    """Confirma o e-mail e redireciona para criação de senha."""

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            usuario = Usuario.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            usuario = None

        if usuario and token_confirmacao.check_token(usuario, token):
            usuario.email_confirmado = True
            usuario.save()
            uid_enc = urlsafe_base64_encode(force_bytes(usuario.pk))
            messages.success(request, 'E-mail confirmado! Agora crie sua senha para acessar o sistema.')
            return redirect('contas:criar_senha', uidb64=uid_enc, token=token)

        messages.error(request, 'Link inválido ou expirado. Tente se cadastrar novamente.')
        return redirect('contas:login')


class CriarSenhaView(View):
    """Permite ao usuário criar a senha após confirmação de e-mail."""

    template_name = 'contas/criar_senha.html'

    def _obter_usuario(self, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            usuario = Usuario.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return None
        if not usuario.email_confirmado:
            return None
        return usuario

    def get(self, request, uidb64, token):
        usuario = self._obter_usuario(uidb64, token)
        if not usuario:
            messages.error(request, 'Link inválido. Solicite um novo cadastro.')
            return redirect('contas:login')
        form = FormCriarSenha()
        return render(request, self.template_name, {'form': form})

    def post(self, request, uidb64, token):
        usuario = self._obter_usuario(uidb64, token)
        if not usuario:
            messages.error(request, 'Link inválido. Solicite um novo cadastro.')
            return redirect('contas:login')
        form = FormCriarSenha(request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['senha'])
            usuario.is_active = True
            usuario.save()
            messages.success(request, 'Senha criada com sucesso! Faça login para continuar.')
            return redirect('contas:login')
        return render(request, self.template_name, {'form': form})


class LoginUsuarioView(View):
    """Login exclusivamente por CPF."""

    template_name = 'contas/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('painel:dashboard')
            return redirect('jogos:inicio')
        form = FormLoginUsuario()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = FormLoginUsuario(request.POST)
        if form.is_valid():
            cpf = form.cleaned_data['cpf']
            senha = form.cleaned_data['senha']

            usuario = authenticate(request, username=cpf, password=senha)

            if usuario:
                if not usuario.email_confirmado:
                    messages.warning(request, 'Confirme seu e-mail antes de fazer login.')
                    return render(request, self.template_name, {'form': form})
                login(request, usuario)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if usuario.is_staff:
                    return redirect('painel:dashboard')
                return redirect('jogos:inicio')

            messages.error(request, 'Credenciais inválidas. Verifique seu CPF e senha.')
        return render(request, self.template_name, {'form': form})

class LogoutUsuarioView(View):
    """Encerra a sessão do usuário."""

    def post(self, request):
        logout(request)
        messages.info(request, 'Você saiu da plataforma com segurança.')
        return redirect('contas:login')

