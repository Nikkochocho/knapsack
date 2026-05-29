"""
ui/report_exporter.py
=====================
Geração do relatório PDF de Análise Comparativa.
Requer: pip install reportlab
"""


import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

from reportlab.lib.pagesizes   import A4
from reportlab.lib.units       import cm
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums       import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib             import colors
from reportlab.platypus        import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, HRFlowable,
)

import config
from ui.report_texts import (
    TITULO, SUBTITULO, INTEGRANTES, INSTITUICAO, ANO,
    SEC1_TITULO, SEC1_TEXTO,
    SEC2_TITULO, SEC2_TEXTO,
    SEC3_TITULO, SEC3_INTRO, SEC3_CONCLUSAO_TEMPLATE,
)


# ── estilos ───────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        'capa_titulo': s('CapaTitulo',
            fontName='Times-Bold', fontSize=18,
            leading=26, alignment=TA_CENTER,
            spaceAfter=16),

        'capa_subtitulo': s('CapaSubtitulo',
            fontName='Times-Italic', fontSize=14,
            leading=20, alignment=TA_CENTER,
            spaceAfter=40),

        'capa_label': s('CapaLabel',
            fontName='Times-Bold', fontSize=12,
            leading=18, alignment=TA_CENTER,
            spaceAfter=4),

        'capa_integrante': s('CapaIntegrante',
            fontName='Times-Roman', fontSize=12,
            leading=18, alignment=TA_CENTER,
            spaceAfter=2),

        'capa_rodape': s('CapaRodape',
            fontName='Times-Roman', fontSize=11,
            leading=16, alignment=TA_CENTER,
            spaceAfter=0),

        'sec_titulo': s('SecTitulo',
            fontName='Times-Bold', fontSize=13,
            leading=20, alignment=TA_LEFT,
            spaceBefore=12, spaceAfter=8),

        'body': s('Body',
            fontName='Times-Roman', fontSize=12,
            leading=20, alignment=TA_JUSTIFY,
            spaceAfter=8),

        'table_header': s('TableHeader',
            fontName='Times-Bold', fontSize=10,
            leading=14, alignment=TA_CENTER),

        'table_cell': s('TableCell',
            fontName='Times-Roman', fontSize=10,
            leading=14, alignment=TA_LEFT),

        'conclusao': s('Conclusao',
            fontName='Times-Italic', fontSize=12,
            leading=20, alignment=TA_JUSTIFY,
            spaceBefore=12, spaceAfter=8),
    }

def _build_chart_reportlab(results: list[dict], width: float) -> Table:
    """Gera o gráfico de barras como Drawing do reportlab."""
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from reportlab.graphics        import renderPDF

    data = [(r['method'], r['gain'] * 100)
            for r in results if r['gain'] is not None]
    if not data:
        return None

    W, H   = width, 180
    PAD_L, PAD_R = 50, 20
    PAD_T, PAD_B = 20, 40
    GAP    = 0.3
    n      = len(data)
    plot_w = W - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B
    slot_w = plot_w / n
    bar_w  = slot_w * (1 - GAP)
    max_v  = max(v for _, v in data)
    max_v  = max(max_v, 1)

    BAR_COLS = ['#4A9EFF','#F5A623','#7ED321','#D0021B',
                '#9B59B6','#1ABC9C','#E67E22','#2ECC71']

    d = Drawing(W, H)

    # grade e eixo Y
    for pct in [0, 25, 50, 75, 100]:
        if pct > max_v + 5:
            continue
        y = PAD_B + (pct / max_v) * plot_h
        d.add(Line(PAD_L, y, W - PAD_R, y,
                   strokeColor=colors.HexColor('#CCCCCC'),
                   strokeDashArray=[3, 3], strokeWidth=0.5))
        d.add(String(PAD_L - 4, y - 4, f'{pct}%',
                     fontSize=7, fillColor=colors.HexColor('#666666'),
                     textAnchor='end'))

    # barras
    for idx, (label, value) in enumerate(data):
        x0    = PAD_L + idx * slot_w + slot_w * GAP / 2
        bar_h = max((value / max_v) * plot_h, 2)
        y0    = PAD_B
        col   = colors.HexColor(BAR_COLS[idx % len(BAR_COLS)])

        d.add(Rect(x0, y0, bar_w, bar_h,
                   fillColor=col, strokeColor=None))
        # valor em cima
        d.add(String(x0 + bar_w / 2, y0 + bar_h + 4,
                     f'{value:.1f}%',
                     fontSize=8, fillColor=colors.HexColor('#222222'),
                     textAnchor='middle'))
        # rótulo abaixo
        d.add(String(x0 + bar_w / 2, PAD_B - 16,
                     label,
                     fontSize=8, fillColor=col,
                     textAnchor='middle'))

    # eixos
    d.add(Line(PAD_L, PAD_B, W - PAD_R, PAD_B,
               strokeColor=colors.HexColor('#AAAAAA'), strokeWidth=1))
    d.add(Line(PAD_L, PAD_B, PAD_L, PAD_B + plot_h,
               strokeColor=colors.HexColor('#AAAAAA'), strokeWidth=1))

    from reportlab.graphics import renderPDF
    from reportlab.platypus import flowables
    return d

# ── tabela de resultados ──────────────────────────────────────────────────────

def _build_results_table(results: list[dict], styles: dict) -> Table:
    header = ['MÉTODO', 'CONFIGURAÇÃO', 'TEMPO (s)', 'GANHO', 'NÓS']
    rows   = [header]

    for r in results:
        gain_str  = f"{r['gain']*100:.1f}%" if r['gain'] is not None else '—'
        time_str  = f"{r['time']:.3f}"      if r['time'] is not None else '—'
        nodes_str = str(r['path_len'])       if r['found'] else '—'
        rows.append([
            r['method'],
            r['config'],
            time_str,
            gain_str,
            nodes_str,
        ])

    col_widths = [2.5*cm, 8.5*cm, 2.5*cm, 2.0*cm, 1.5*cm]

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # cabeçalho
        ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR',   (0, 0), (-1, 0), colors.white),
        ('FONTNAME',    (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE',    (0, 0), (-1, 0), 10),
        ('ALIGN',       (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING',    (0, 0), (-1, 0), 8),
        # linhas de dados
        ('FONTNAME',    (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE',    (0, 1), (-1, -1), 10),
        ('ALIGN',       (2, 1), (-1, -1), 'CENTER'),
        ('ALIGN',       (0, 1), (1, -1),  'LEFT'),
        ('TOPPADDING',  (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        # zebra
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F2F2F2'))
          for i in range(2, len(rows), 2)],
        # bordas
        ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#AAAAAA')),
        ('BOX',         (0, 0), (-1, -1), 1.0, colors.HexColor('#2C3E50')),
    ]))
    return table


# ── conclusão dinâmica ────────────────────────────────────────────────────────

def _build_conclusao(results: list[dict]) -> str:
    validos = [r for r in results if r['gain'] is not None and r['found']]
    if not validos:
        return "Não foi possível determinar o melhor resultado pois nenhum algoritmo encontrou uma solução válida."

    melhor = max(validos, key=lambda r: r['gain'])
    return SEC3_CONCLUSAO_TEMPLATE.format(
        method=melhor['method'],
        config=melhor['config'] if melhor['config'] != '—' else 'padrão',
        time=f"{melhor['time']:.3f}",
        limit=f"{config.TEMPO_LIMITE:.1f}",
        gain=f"{melhor['gain']*100:.1f}",
    )


# ── geração do PDF ────────────────────────────────────────────────────────────

def export_report(results: list[dict]):
    """Abre diálogo para salvar e gera o PDF do relatório."""

    path = filedialog.asksaveasfilename(
        title='Salvar relatório',
        defaultextension='.pdf',
        filetypes=[('PDF', '*.pdf')],
        initialfile=f'relatorio_ia.pdf',
    )
    if not path:
        return

    styles  = _build_styles()
    W, H    = A4
    margin  = 3 * cm

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin,  bottomMargin=margin,
        title=TITULO,
    )

    story = []

    # ── CAPA ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph(TITULO,    styles['capa_titulo']))
    story.append(Paragraph(SUBTITULO, styles['capa_subtitulo']))
    story.append(HRFlowable(width='80%', thickness=1,
                             color=colors.HexColor('#2C3E50'),
                             spaceAfter=24, spaceBefore=0))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph('Integrantes:', styles['capa_label']))
    for nome in INTEGRANTES:
        story.append(Paragraph(nome, styles['capa_integrante']))

    if INSTITUICAO:
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph(INSTITUICAO, styles['capa_rodape']))
    if ANO:
        story.append(Paragraph(ANO, styles['capa_rodape']))

    story.append(PageBreak())

    # ── SEÇÃO 1 — INTRODUÇÃO ──────────────────────────────────────────────────
    story.append(Paragraph(SEC1_TITULO, styles['sec_titulo']))
    story.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#AAAAAA'),
                             spaceAfter=10))
    for paragrafo in SEC1_TEXTO.split('\n\n'):
        if paragrafo.strip():
            story.append(Paragraph(paragrafo.strip(), styles['body']))

    story.append(PageBreak())

    # ── SEÇÃO 2 — METODOLOGIA ─────────────────────────────────────────────────
    story.append(Paragraph(SEC2_TITULO, styles['sec_titulo']))
    story.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#AAAAAA'),
                             spaceAfter=10))
    for paragrafo in SEC2_TEXTO.split('\n\n'):
        if paragrafo.strip():
            story.append(Paragraph(paragrafo.strip(), styles['body']))

    story.append(PageBreak())

    # ── SEÇÃO 3 — RESULTADOS ──────────────────────────────────────────────────
    story.append(Paragraph(SEC3_TITULO, styles['sec_titulo']))
    story.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#AAAAAA'),
                             spaceAfter=10))
    story.append(Paragraph(SEC3_INTRO, styles['body']))
    story.append(Spacer(1, 0.4 * cm))

    n_mapas = (f"{config.MULTIVERSE.n_maps} mapas"
           if config.MULTIVERSE_MODE and config.MULTIVERSE
           else "mapa simples")

    contexto = (
        f"Configuração da execução: limite de tempo de "
        f"<b>{config.TEMPO_LIMITE:.1f}s</b>, {n_mapas}, "
        f"nó inicial <b>{config.START_NODE}</b>, "
        f"nó objetivo <b>{config.GOAL_NODE}</b>."
    )
    story.append(Paragraph(contexto, styles['body']))
    story.append(Spacer(1, 0.3 * cm))

    # tabela
    story.append(_build_results_table(results, styles))
    story.append(Spacer(1, 0.6 * cm))

    # gráfico
    chart = _build_chart_reportlab(results, W - 2 * margin)
    if chart is not None:
        story.append(chart)
        story.append(Spacer(1, 0.6 * cm))

    # conclusão
    story.append(Paragraph(_build_conclusao(results), styles['conclusao']))

    # ── build ──────────────────────────────────────────────────────────────────
    try:
        doc.build(story)
        messagebox.showinfo('Relatório exportado',
                            f'PDF salvo com sucesso em:\n{path}')
    except Exception as e:
        messagebox.showerror('Erro ao exportar', str(e))