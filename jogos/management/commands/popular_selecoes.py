from django.core.management.base import BaseCommand
from jogos.models import Selecao


SELECOES = [
    # nome, sigla, icone (emoji bandeira)
    # CONMEBOL
    ('Argentina',      'ARG', '🇦🇷'),
    ('Brasil',         'BRA', '🇧🇷'),
    ('Colômbia',       'COL', '🇨🇴'),
    ('Uruguai',        'URU', '🇺🇾'),
    ('Equador',        'ECU', '🇪🇨'),
    ('Paraguai',       'PAR', '🇵🇾'),
    ('Venezuela',      'VEN', '🇻🇪'),
    ('Bolívia',        'BOL', '🇧🇴'),
    # CONCACAF
    ('Estados Unidos', 'USA', '🇺🇸'),
    ('Canadá',         'CAN', '🇨🇦'),
    ('México',         'MEX', '🇲🇽'),
    ('Panamá',         'PAN', '🇵🇦'),
    ('Costa Rica',     'CRC', '🇨🇷'),
    ('Honduras',       'HON', '🇭🇳'),
    ('Jamaica',        'JAM', '🇯🇲'),
    ('Guatemala',      'GUA', '🇬🇹'),
    # UEFA
    ('Alemanha',       'GER', '🇩🇪'),
    ('Espanha',        'ESP', '🇪🇸'),
    ('França',         'FRA', '🇫🇷'),
    ('Inglaterra',     'ENG', '🏴󠁧󠁢󠁥󠁮󠁧󠁿'),
    ('Portugal',       'POR', '🇵🇹'),
    ('Holanda',        'NED', '🇳🇱'),
    ('Bélgica',        'BEL', '🇧🇪'),
    ('Itália',         'ITA', '🇮🇹'),
    ('Áustria',        'AUT', '🇦🇹'),
    ('Croácia',        'CRO', '🇭🇷'),
    ('Suíça',          'SUI', '🇨🇭'),
    ('Dinamarca',      'DEN', '🇩🇰'),
    ('Turquia',        'TUR', '🇹🇷'),
    ('Polônia',        'POL', '🇵🇱'),
    ('Escócia',        'SCO', '🏴󠁧󠁢󠁳󠁣󠁴󠁿'),
    ('Eslováquia',     'SVK', '🇸🇰'),
    ('Hungria',        'HUN', '🇭🇺'),
    ('Romênia',        'ROU', '🇷🇴'),
    # AFC (Ásia)
    ('Japão',          'JPN', '🇯🇵'),
    ('Coreia do Sul',  'KOR', '🇰🇷'),
    ('Austrália',      'AUS', '🇦🇺'),
    ('Irã',            'IRN', '🇮🇷'),
    ('Arábia Saudita', 'KSA', '🇸🇦'),
    ('Qatar',          'QAT', '🇶🇦'),
    ('Uzbequistão',    'UZB', '🇺🇿'),
    ('Jordânia',       'JOR', '🇯🇴'),
    ('Omã',            'OMA', '🇴🇲'),
    # CAF (África)
    ('Marrocos',       'MAR', '🇲🇦'),
    ('Senegal',        'SEN', '🇸🇳'),
    ('Egito',          'EGY', '🇪🇬'),
    ('Nigéria',        'NGA', '🇳🇬'),
    ('Camarões',       'CMR', '🇨🇲'),
    ('África do Sul',  'RSA', '🇿🇦'),
    ('Costa do Marfim','CIV', '🇨🇮'),
    ('Argélia',        'ALG', '🇩🇿'),
    ('Gana',           'GHA', '🇬🇭'),
    ('Tunísia',        'TUN', '🇹🇳'),
    ('Mali',           'MLI', '🇲🇱'),
    ('Rep. Democrática do Congo', 'COD', '🇨🇩'),
    # OFC
    ('Nova Zelândia',  'NZL', '🇳🇿'),
]


class Command(BaseCommand):
    help = 'Popula o banco com todas as seleções da Copa do Mundo 2026'

    def handle(self, *args, **options):
        criadas = 0
        atualizadas = 0
        for nome, sigla, icone in SELECOES:
            obj, criado = Selecao.objects.update_or_create(
                sigla=sigla,
                defaults={'nome': nome, 'icone': icone},
            )
            if criado:
                criadas += 1
            else:
                atualizadas += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Concluído: {criadas} seleções criadas, {atualizadas} atualizadas. Total: {criadas + atualizadas}.'
        ))
