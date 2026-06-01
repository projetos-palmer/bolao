from django.core.management.base import BaseCommand
from boloes.services import verificar_boloes_para_fechar
from boloes.models import Bolao
from django.utils import timezone


class Command(BaseCommand):
    help = 'Fecha automaticamente bolões cujo prazo de apostas já encerrou.'

    def handle(self, *args, **options):
        abertos_antes = Bolao.objects.filter(status='aberto').count()
        verificar_boloes_para_fechar()
        abertos_depois = Bolao.objects.filter(status='aberto').count()
        fechados = abertos_antes - abertos_depois
        self.stdout.write(
            self.style.SUCCESS(
                f'[{timezone.now():%d/%m/%Y %H:%M:%S}] {fechados} bolão(ões) fechado(s).'
            )
        )
