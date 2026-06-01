from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pagamentos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracaopixadministrador',
            name='client_id_efi',
            field=models.CharField(blank=True, help_text='Client ID da aplicação EFI Bank (ex-Gerencianet)', max_length=200, verbose_name='Client ID (EFI Bank)'),
        ),
        migrations.AddField(
            model_name='configuracaopixadministrador',
            name='client_secret_efi',
            field=models.CharField(blank=True, help_text='Client Secret da aplicação EFI Bank', max_length=200, verbose_name='Client Secret (EFI Bank)'),
        ),
        migrations.AddField(
            model_name='configuracaopixadministrador',
            name='certificado_efi',
            field=models.FileField(blank=True, help_text='Arquivo de certificado mTLS (.p12 ou .pem) gerado no portal EFI Bank', null=True, upload_to='certificados/', verbose_name='Certificado EFI (.p12/.pem)'),
        ),
        migrations.AddField(
            model_name='configuracaopixadministrador',
            name='ambiente_efi',
            field=models.CharField(choices=[('homologacao', 'Homologação (testes)'), ('producao', 'Produção')], default='homologacao', help_text='Use Homologação para testes e Produção para cobranças reais', max_length=20, verbose_name='Ambiente EFI'),
        ),
    ]
