from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pagamentos', '0003_lote_pagamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracaopixadministrador',
            name='mp_access_token',
            field=models.CharField(
                blank=True,
                help_text='Access Token de produção da sua conta Mercado Pago (começa com APP_USR-...). '
                          'Se preenchido, o Mercado Pago será usado com prioridade sobre o EFI Bank.',
                max_length=300,
                verbose_name='Access Token (Mercado Pago)',
            ),
        ),
    ]
