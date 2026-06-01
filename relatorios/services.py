import io
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from boloes.models import Bolao, Premio


def gerar_pdf_relatorio_bolao(bolao_pk: int) -> bytes:
    """Gera o PDF de relatório de um bolão. Retorna bytes do PDF."""
    bolao = Bolao.objects.select_related('jogo__selecao_mandante', 'jogo__selecao_visitante').get(pk=bolao_pk)
    participacoes = bolao.participacoes.filter(
        status__in=['confirmado', 'valido', 'vencedor', 'nao_premiado', 'premio_pago']
    ).select_related('usuario')
    premios = Premio.objects.filter(bolao=bolao).select_related('usuario')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    estilos = getSampleStyleSheet()
    verde = colors.HexColor('#16a34a')
    amarelo = colors.HexColor('#ca8a04')

    elementos = []

    # Título
    titulo_style = ParagraphStyle('titulo', parent=estilos['Title'], textColor=verde, fontSize=18)
    elementos.append(Paragraph('⚽ Relatório do Bolão', titulo_style))
    elementos.append(Paragraph(bolao.nome, estilos['Heading2']))
    elementos.append(Spacer(1, 0.5*cm))

    # Informações do jogo
    jogo = bolao.jogo
    info_jogo = [
        ['Jogo:', f'{jogo.selecao_mandante} x {jogo.selecao_visitante}'],
        ['Data/Hora:', jogo.data_hora.strftime('%d/%m/%Y às %H:%M')],
        ['Estádio:', jogo.estadio or '—'],
        ['Resultado:', f'{jogo.placar_mandante} x {jogo.placar_visitante}' if jogo.resultado_definido else 'Não informado'],
    ]
    tabela_jogo = Table(info_jogo, colWidths=[4*cm, 12*cm])
    tabela_jogo.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), verde),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela_jogo)
    elementos.append(Spacer(1, 0.5*cm))

    # Resumo financeiro
    total_arrecadado = bolao.valor_total_arrecadado
    total_premio = bolao.valor_total_premio
    retido = total_arrecadado - total_premio

    info_financeiro = [
        ['Valor de participação:', f'R$ {bolao.valor_participacao:.2f}'],
        ['Total de participações:', str(participacoes.count())],
        ['Total arrecadado:', f'R$ {total_arrecadado:.2f}'],
        ['Percentual premiação:', f'{bolao.percentual_premiacao}%'],
        ['Valor do prêmio:', f'R$ {total_premio:.2f}'],
        ['Valor retido:', f'R$ {retido:.2f}'],
    ]
    tabela_fin = Table(info_financeiro, colWidths=[6*cm, 10*cm])
    tabela_fin.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), amarelo),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(Paragraph('Resumo Financeiro', estilos['Heading3']))
    elementos.append(tabela_fin)
    elementos.append(Spacer(1, 0.5*cm))

    # Lista de participações
    elementos.append(Paragraph('Participantes e Palpites', estilos['Heading3']))
    cabecalho = ['Usuário', 'Palpite', 'Status']
    dados_participacoes = [cabecalho]
    for p in participacoes:
        dados_participacoes.append([
            p.usuario.nome_completo,
            f'{p.placar_mandante} x {p.placar_visitante}',
            p.get_status_display(),
        ])
    tab_part = Table(dados_participacoes, colWidths=[7*cm, 4*cm, 5*cm])
    tab_part.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), verde),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tab_part)
    elementos.append(Spacer(1, 0.5*cm))

    # Ganhadores
    elementos.append(Paragraph('Ganhadores e Prêmios', estilos['Heading3']))
    if premios.exists():
        dados_premios = [['Ganhador', 'Valor do Prêmio', 'Status Pgto']]
        for premio in premios:
            dados_premios.append([
                premio.usuario.nome_completo,
                f'R$ {premio.valor:.2f}',
                premio.get_status_pagamento_display(),
            ])
        tab_premios = Table(dados_premios, colWidths=[7*cm, 5*cm, 4*cm])
        tab_premios.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), amarelo),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tab_premios)
    else:
        elementos.append(Paragraph('Nenhum ganhador encontrado.', estilos['Normal']))

    elementos.append(Spacer(1, 1*cm))
    rodape = f'Gerado em: {timezone.now().strftime("%d/%m/%Y às %H:%M")}'
    elementos.append(Paragraph(rodape, estilos['Normal']))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.read()
