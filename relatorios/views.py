from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404

from boloes.models import Bolao
from .services import gerar_pdf_relatorio_bolao


class AdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class RelatorioBolaoPDFView(AdminMixin, View):
    """Gera e retorna o PDF de relatório de um bolão."""

    def get(self, request, pk):
        get_object_or_404(Bolao, pk=pk)
        pdf_bytes = gerar_pdf_relatorio_bolao(pk)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio-bolao-{pk}.pdf"'
        return response
