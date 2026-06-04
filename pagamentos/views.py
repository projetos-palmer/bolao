import json
import logging

from django.views.generic import DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from boloes.models import ParticipacaoBolao
from .models import Pagamento, PagamentoLote, ConfiguracaoPixAdministrador
from .pix import criar_pagamento, criar_pagamento_lote, registrar_webhook_efi, tem_credenciais_efi
from .pix_mp import MercadoPagoError, tem_credenciais_mp, verificar_pagamento_mp

logger = logging.getLogger(__name__)


def _pagamento_foi_criado_no_mp(pagamento):
    return bool(pagamento.txid and pagamento.txid.isdigit())


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class PagamentoPixDetailView(LoginRequiredMixin, View):
    """Exibe o QR Code e pix copia e cola para o usuário pagar."""

    template_name = 'pagamentos/pagamento_pix.html'

    def get(self, request, participacao_pk):
        participacao = get_object_or_404(
            ParticipacaoBolao,
            pk=participacao_pk,
            usuario=request.user,
        )

        # Cria ou recupera pagamento
        pagamento = Pagamento.objects.filter(participacao=participacao).first()
        config_pix = ConfiguracaoPixAdministrador.objects.filter(ativo=True).first()
        if not config_pix:
            messages.error(request, 'Chave Pix do administrador nao configurada. Contate o suporte.')
            return redirect('boloes:meus_jogos')

        if pagamento and pagamento.status == 'pendente' and tem_credenciais_mp(config_pix) and not _pagamento_foi_criado_no_mp(pagamento):
            logger.warning('Removendo PIX estatico pendente para recriar no Mercado Pago: pagamento=%s txid=%s', pagamento.pk, pagamento.txid)
            pagamento.delete()
            pagamento = None

        if not pagamento:
            try:
                pagamento = criar_pagamento(participacao, config_pix)
            except MercadoPagoError as exc:
                logger.exception('Falha ao criar cobranca Mercado Pago para participacao %s', participacao.pk)
                messages.error(request, f'Erro ao gerar PIX pelo Mercado Pago: {exc}')
                return redirect('boloes:meus_jogos')

        # Verifica expiração
        if pagamento.esta_expirado:
            pagamento.status = 'expirado'
            pagamento.save(update_fields=['status'])
            participacao.status = 'expirado'
            participacao.save(update_fields=['status'])
            messages.warning(request, 'O prazo de 3 minutos para pagamento expirou. Faça uma nova participação se o bolão ainda estiver aberto.')
            return redirect('boloes:bolao_detail', pk=participacao.bolao.pk)

        confirmacao_automatica = (
            (tem_credenciais_mp(config_pix) or tem_credenciais_efi(config_pix))
            if config_pix else False
        )

        return render(request, self.template_name, {
            'participacao': participacao,
            'pagamento': pagamento,
            'confirmacao_automatica': confirmacao_automatica,
        })


class StatusPagamentoView(LoginRequiredMixin, View):
    """Retorna o status atual do pagamento como JSON — usado pelo polling do frontend."""

    def get(self, request, pk):
        pagamento = get_object_or_404(
            Pagamento,
            pk=pk,
            participacao__usuario=request.user,
        )
        url_confirmado = None
        if pagamento.status == 'confirmado':
            url_confirmado = reverse('pagamentos:pagamento_confirmado', args=[pagamento.pk])
        return JsonResponse({
            'status': pagamento.status,
            'confirmado': pagamento.status == 'confirmado',
            'expirado': pagamento.status == 'expirado' or pagamento.esta_expirado,
            'url_confirmado': url_confirmado,
        })


@method_decorator(csrf_exempt, name='dispatch')
class WebhookPixEfiView(View):
    """
    Recebe notificações de pagamento PIX enviadas pelo EFI Bank.
    Esta URL deve ser registrada no painel EFI Bank como webhook.
    Não requer autenticação de sessão (chamada feita pelo servidor EFI Bank).
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'erro': 'corpo inválido'}, status=400)

        for pix in data.get('pix', []):
            txid = pix.get('txid', '').strip()
            if not txid:
                continue
            # Tenta confirmar lote primeiro (txid começa com 'L' ou é do lote)
            lote_confirmado = False
            try:
                lote = PagamentoLote.objects.get(txid=txid, status='pendente')
                lote.status = 'confirmado'
                lote.data_confirmacao = timezone.now()
                lote.save(update_fields=['status', 'data_confirmacao'])
                # Confirma todos os pagamentos e participações do lote
                for pag in lote.pagamentos.select_related('participacao').all():
                    pag.status = 'confirmado'
                    pag.data_confirmacao = lote.data_confirmacao
                    pag.save(update_fields=['status', 'data_confirmacao'])
                    pag.participacao.status = 'confirmado'
                    pag.participacao.save(update_fields=['status'])
                lote_confirmado = True
                logger.info('Lote %s confirmado via webhook EFI: txid=%s', lote.pk, txid)
            except PagamentoLote.DoesNotExist:
                pass

            if not lote_confirmado:
                try:
                    pagamento = Pagamento.objects.select_related('participacao').get(
                        txid=txid,
                        status='pendente',
                    )
                    pagamento.status = 'confirmado'
                    pagamento.data_confirmacao = timezone.now()
                    pagamento.save(update_fields=['status', 'data_confirmacao'])

                    participacao = pagamento.participacao
                    participacao.status = 'confirmado'
                    participacao.save(update_fields=['status'])

                    logger.info('Pagamento confirmado automaticamente via webhook EFI: txid=%s', txid)
                except Pagamento.DoesNotExist:
                    logger.warning('Webhook EFI recebido para txid desconhecido ou já confirmado: %s', txid)

        return JsonResponse({'ok': True})


class RegistrarWebhookEfiView(AdminMixin, View):
    """Registra a URL de webhook no EFI Bank para receber notificações automáticas de PIX."""

    def post(self, request):
        config_pix = ConfiguracaoPixAdministrador.objects.filter(ativo=True).first()
        if not config_pix or not tem_credenciais_efi(config_pix):
            messages.error(request, 'Configure as credenciais EFI Bank antes de registrar o webhook.')
            return redirect('painel:configuracao_pix')

        webhook_url = request.build_absolute_uri(reverse('pagamentos:webhook_pix_efi'))
        try:
            registrar_webhook_efi(config_pix, webhook_url)
            messages.success(request, f'Webhook EFI Bank registrado com sucesso: {webhook_url}')
        except Exception as exc:
            messages.error(request, f'Erro ao registrar webhook: {exc}')

        return redirect('painel:dashboard')


class ConfirmarPagamentoView(AdminMixin, View):
    """Confirma manualmente um pagamento (admin)."""

    def post(self, request, pk):
        pagamento = get_object_or_404(Pagamento, pk=pk)

        if pagamento.status == 'confirmado':
            messages.info(request, 'Este pagamento já foi confirmado.')
            return redirect('painel:dashboard')

        pagamento.status = 'confirmado'
        pagamento.data_confirmacao = timezone.now()
        pagamento.confirmado_por = request.user
        pagamento.save(update_fields=['status', 'data_confirmacao', 'confirmado_por'])

        participacao = pagamento.participacao
        participacao.status = 'confirmado'
        participacao.save(update_fields=['status'])

        messages.success(request, f'Pagamento de {participacao.usuario.nome_completo} confirmado!')
        return redirect('painel:dashboard')


class PagamentoConfirmadoView(LoginRequiredMixin, DetailView):
    model = Pagamento
    template_name = 'pagamentos/pagamento_confirmado.html'
    context_object_name = 'pagamento'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['participacao'] = self.object.participacao
        return ctx


# ---------------------------------------------------------------------------
# Pagamento em lote
# ---------------------------------------------------------------------------

class PagamentoLoteCreateView(LoginRequiredMixin, View):
    """
    Recebe POST com lista de IDs de participações, cria um PagamentoLote
    com valor total e redireciona para a tela de pagamento do lote.
    """

    def post(self, request):
        ids = request.POST.getlist('participacoes')
        if not ids:
            messages.warning(request, 'Selecione ao menos um bolão para pagar.')
            return redirect('boloes:meus_jogos')

        participacoes = list(
            ParticipacaoBolao.objects.filter(
                pk__in=ids,
                usuario=request.user,
                status='aguardando',
            ).select_related('bolao')
        )
        if not participacoes:
            messages.warning(request, 'Nenhuma participação válida encontrada para pagamento.')
            return redirect('boloes:meus_jogos')

        config_pix = ConfiguracaoPixAdministrador.objects.filter(ativo=True).first()
        if not config_pix:
            messages.error(request, 'Chave Pix do administrador não configurada. Contate o suporte.')
            return redirect('boloes:meus_jogos')

        try:
            lote = criar_pagamento_lote(participacoes, config_pix, request.user)
        except MercadoPagoError as exc:
            logger.exception('Falha ao criar cobranca Mercado Pago em lote para usuario %s', request.user.pk)
            messages.error(request, f'Erro ao gerar PIX pelo Mercado Pago: {exc}')
            return redirect('boloes:meus_jogos')
        return redirect('pagamentos:pagamento_lote', pk=lote.pk)


class PagamentoLoteDetailView(LoginRequiredMixin, View):
    """Exibe QR Code do lote e aguarda confirmação."""

    template_name = 'pagamentos/pagamento_lote.html'

    def get(self, request, pk):
        lote = get_object_or_404(PagamentoLote, pk=pk, usuario=request.user)
        config_pix = ConfiguracaoPixAdministrador.objects.filter(ativo=True).first()

        if lote.status == 'pendente' and tem_credenciais_mp(config_pix) and not _pagamento_foi_criado_no_mp(lote):
            logger.warning('Removendo PIX estatico pendente de lote para recriar no Mercado Pago: lote=%s txid=%s', lote.pk, lote.txid)
            participacoes = list(ParticipacaoBolao.objects.filter(pagamento__lote=lote).select_related('bolao'))
            lote.pagamentos.all().delete()
            lote.delete()
            try:
                novo_lote = criar_pagamento_lote(participacoes, config_pix, request.user)
            except MercadoPagoError as exc:
                logger.exception('Falha ao recriar cobranca Mercado Pago em lote %s', pk)
                messages.error(request, f'Erro ao gerar PIX pelo Mercado Pago: {exc}')
                return redirect('boloes:meus_jogos')
            return redirect('pagamentos:pagamento_lote', pk=novo_lote.pk)

        if lote.esta_expirado and lote.status == 'pendente':
            lote.status = 'expirado'
            lote.save(update_fields=['status'])
            lote.pagamentos.all().update(status='expirado')
            ParticipacaoBolao.objects.filter(pagamento__lote=lote).update(status='expirado')
            messages.warning(request, 'O prazo de pagamento expirou. Faça novas apostas se os bolões ainda estiverem abertos.')
            return redirect('boloes:meus_jogos')

        confirmacao_automatica = (
            (tem_credenciais_mp(config_pix) or tem_credenciais_efi(config_pix))
            if config_pix else False
        )

        participacoes = ParticipacaoBolao.objects.filter(
            pagamento__lote=lote
        ).select_related('bolao__jogo__selecao_mandante', 'bolao__jogo__selecao_visitante')

        return render(request, self.template_name, {
            'lote': lote,
            'participacoes': participacoes,
            'confirmacao_automatica': confirmacao_automatica,
        })


class StatusPagamentoLoteView(LoginRequiredMixin, View):
    """JSON polling para a tela de pagamento do lote."""

    def get(self, request, pk):
        lote = get_object_or_404(PagamentoLote, pk=pk, usuario=request.user)
        url_confirmado = None
        if lote.status == 'confirmado':
            url_confirmado = reverse('pagamentos:lote_confirmado', args=[lote.pk])
        return JsonResponse({
            'status': lote.status,
            'confirmado': lote.status == 'confirmado',
            'expirado': lote.status == 'expirado' or lote.esta_expirado,
            'url_confirmado': url_confirmado,
        })


@method_decorator(csrf_exempt, name='dispatch')
class WebhookPixMPView(View):
    """
    Recebe notificações de pagamento do Mercado Pago.
    Esta URL deve ser registrada no painel MP como webhook de Pagamentos.
    Não requer autenticação de sessão (chamada feita pelo servidor do MP).
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'erro': 'corpo inválido'}, status=400)

        # MP envia: {"type": "payment", "data": {"id": "12345"}}
        if data.get('type') != 'payment':
            return JsonResponse({'ok': 'ignorado'}, status=200)

        mp_payment_id = str(data.get('data', {}).get('id', '')).strip()
        if not mp_payment_id:
            return JsonResponse({'erro': 'id ausente'}, status=400)

        try:
            config_pix = ConfiguracaoPixAdministrador.objects.filter(ativo=True).first()
            if not config_pix:
                return JsonResponse({'erro': 'sem configuração ativa'}, status=500)
            info = verificar_pagamento_mp(config_pix, mp_payment_id)
        except Exception as exc:
            logger.error('Webhook MP: erro ao verificar pagamento %s: %s', mp_payment_id, exc)
            return JsonResponse({'erro': 'falha ao verificar pagamento'}, status=500)

        if info.get('status') != 'approved':
            return JsonResponse({'ok': 'não aprovado ainda'}, status=200)

        # Tenta confirmar lote (txid = mp_payment_id)
        lote_confirmado = False
        try:
            lote = PagamentoLote.objects.get(txid=mp_payment_id, status='pendente')
            lote.status = 'confirmado'
            lote.data_confirmacao = timezone.now()
            lote.save(update_fields=['status', 'data_confirmacao'])
            for pag in lote.pagamentos.select_related('participacao').all():
                pag.status = 'confirmado'
                pag.data_confirmacao = lote.data_confirmacao
                pag.save(update_fields=['status', 'data_confirmacao'])
                pag.participacao.status = 'confirmado'
                pag.participacao.save(update_fields=['status'])
            lote_confirmado = True
            logger.info('Lote %s confirmado via webhook MP: txid=%s', lote.pk, mp_payment_id)
        except PagamentoLote.DoesNotExist:
            pass

        if not lote_confirmado:
            try:
                pagamento = Pagamento.objects.select_related('participacao').get(
                    txid=mp_payment_id,
                    status='pendente',
                )
                pagamento.status = 'confirmado'
                pagamento.data_confirmacao = timezone.now()
                pagamento.save(update_fields=['status', 'data_confirmacao'])
                pagamento.participacao.status = 'confirmado'
                pagamento.participacao.save(update_fields=['status'])
                logger.info('Pagamento confirmado automaticamente via webhook MP: txid=%s', mp_payment_id)
            except Pagamento.DoesNotExist:
                logger.warning('Webhook MP: txid desconhecido ou já confirmado: %s', mp_payment_id)

        return JsonResponse({'ok': True})


class PagamentoLoteConfirmadoView(LoginRequiredMixin, View):
    """Página de confirmação do lote."""

    def get(self, request, pk):
        lote = get_object_or_404(PagamentoLote, pk=pk, usuario=request.user)
        participacoes = ParticipacaoBolao.objects.filter(
            pagamento__lote=lote
        ).select_related('bolao__jogo__selecao_mandante', 'bolao__jogo__selecao_visitante')
        return render(request, 'pagamentos/lote_confirmado.html', {
            'lote': lote,
            'participacoes': participacoes,
        })


