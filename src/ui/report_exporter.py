"""
ui/report_exporter.py
=====================
PDF report generation for the Comparative Analysis.
The report is generated in whichever language is active in the app at
export time (see i18n.get_language()).
Requires: pip install reportlab
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
import i18n
from ui.report_texts import MEMBERS, INSTITUTION, YEAR, get_text


# ── styles ────────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        'cover_title': s('CoverTitle',
            fontName='Times-Bold', fontSize=18,
            leading=26, alignment=TA_CENTER,
            spaceAfter=16),

        'cover_subtitle': s('CoverSubtitle',
            fontName='Times-Italic', fontSize=14,
            leading=20, alignment=TA_CENTER,
            spaceAfter=40),

        'cover_label': s('CoverLabel',
            fontName='Times-Bold', fontSize=12,
            leading=18, alignment=TA_CENTER,
            spaceAfter=4),

        'cover_member': s('CoverMember',
            fontName='Times-Roman', fontSize=12,
            leading=18, alignment=TA_CENTER,
            spaceAfter=2),

        'cover_footer': s('CoverFooter',
            fontName='Times-Roman', fontSize=11,
            leading=16, alignment=TA_CENTER,
            spaceAfter=0),

        'section_title': s('SectionTitle',
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

        'conclusion': s('Conclusion',
            fontName='Times-Italic', fontSize=12,
            leading=20, alignment=TA_JUSTIFY,
            spaceBefore=12, spaceAfter=8),
    }

def _build_chart_reportlab(results: list[dict], width: float) -> Table:
    """Generate the bar chart as a reportlab Drawing."""
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

    # grid and Y axis
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

    # bars
    for idx, (label, value) in enumerate(data):
        x0    = PAD_L + idx * slot_w + slot_w * GAP / 2
        bar_h = max((value / max_v) * plot_h, 2)
        y0    = PAD_B
        col   = colors.HexColor(BAR_COLS[idx % len(BAR_COLS)])

        d.add(Rect(x0, y0, bar_w, bar_h,
                   fillColor=col, strokeColor=None))
        # value label above
        d.add(String(x0 + bar_w / 2, y0 + bar_h + 4,
                     f'{value:.1f}%',
                     fontSize=8, fillColor=colors.HexColor('#222222'),
                     textAnchor='middle'))
        # label below
        d.add(String(x0 + bar_w / 2, PAD_B - 16,
                     label,
                     fontSize=8, fillColor=col,
                     textAnchor='middle'))

    # axes
    d.add(Line(PAD_L, PAD_B, W - PAD_R, PAD_B,
               strokeColor=colors.HexColor('#AAAAAA'), strokeWidth=1))
    d.add(Line(PAD_L, PAD_B, PAD_L, PAD_B + plot_h,
               strokeColor=colors.HexColor('#AAAAAA'), strokeWidth=1))

    from reportlab.graphics import renderPDF
    from reportlab.platypus import flowables
    return d

# ── results table ──────────────────────────────────────────────────────────────

def _build_results_table(results: list[dict], styles: dict, lang: str) -> Table:
    header = get_text('table_headers', lang)
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
        # header
        ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR',   (0, 0), (-1, 0), colors.white),
        ('FONTNAME',    (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE',    (0, 0), (-1, 0), 10),
        ('ALIGN',       (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING',    (0, 0), (-1, 0), 8),
        # data rows
        ('FONTNAME',    (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE',    (0, 1), (-1, -1), 10),
        ('ALIGN',       (2, 1), (-1, -1), 'CENTER'),
        ('ALIGN',       (0, 1), (1, -1),  'LEFT'),
        ('TOPPADDING',  (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        # zebra striping
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F2F2F2'))
          for i in range(2, len(rows), 2)],
        # borders
        ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#AAAAAA')),
        ('BOX',         (0, 0), (-1, -1), 1.0, colors.HexColor('#2C3E50')),
    ]))
    return table


# ── dynamic conclusion ────────────────────────────────────────────────────────

def _build_conclusion(results: list[dict], lang: str) -> str:
    valid = [r for r in results if r['gain'] is not None and r['found']]
    if not valid:
        return get_text('conclusion_no_result', lang)

    best = max(valid, key=lambda r: r['gain'])
    return get_text(
        'conclusion_template', lang,
        method=best['method'],
        config=best['config'] if best['config'] != '—' else get_text('default_config_label', lang),
        time=f"{best['time']:.3f}",
        limit=f"{config.TEMPO_LIMITE:.1f}",
        gain=f"{best['gain']*100:.1f}",
    )


# ── PDF generation ────────────────────────────────────────────────────────────

def export_report(results: list[dict]):
    """Open a save dialog and generate the report PDF, in whichever language
    is currently active in the app."""

    lang = i18n.get_language()

    path = filedialog.asksaveasfilename(
        title=get_text('save_dialog_title', lang),
        defaultextension='.pdf',
        filetypes=[('PDF', '*.pdf')],
        initialfile=get_text('save_filename', lang),
    )
    if not path:
        return

    styles  = _build_styles()
    W, H    = A4
    margin  = 3 * cm

    title    = get_text('title', lang)
    subtitle = get_text('subtitle', lang)

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin,  bottomMargin=margin,
        title=title,
    )

    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph(title,    styles['cover_title']))
    story.append(Paragraph(subtitle, styles['cover_subtitle']))
    story.append(HRFlowable(width='80%', thickness=1,
                             color=colors.HexColor('#2C3E50'),
                             spaceAfter=24, spaceBefore=0))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(get_text('members_label', lang), styles['cover_label']))
    for name in MEMBERS:
        story.append(Paragraph(name, styles['cover_member']))

    if INSTITUTION:
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph(INSTITUTION, styles['cover_footer']))
    if YEAR:
        story.append(Paragraph(YEAR, styles['cover_footer']))

    story.append(PageBreak())

    # ── SECTION 1 — INTRODUCTION ────────────────────────────────────────────
    story.append(Paragraph(get_text('section1_title', lang), styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#AAAAAA'),
                             spaceAfter=10))
    for paragraph in get_text('section1_text', lang).split('\n\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles['body']))

    story.append(PageBreak())

    # ── SECTION 2 — METHODOLOGY ──────────────────────────────────────────────
    story.append(Paragraph(get_text('section2_title', lang), styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#AAAAAA'),
                             spaceAfter=10))
    for paragraph in get_text('section2_text', lang).split('\n\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles['body']))

    story.append(PageBreak())

    # ── SECTION 3 — RESULTS ──────────────────────────────────────────────────
    story.append(Paragraph(get_text('section3_title', lang), styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#AAAAAA'),
                             spaceAfter=10))
    story.append(Paragraph(get_text('section3_intro', lang), styles['body']))
    story.append(Spacer(1, 0.4 * cm))

    if config.MULTIVERSE_MODE and config.MULTIVERSE:
        n_maps = get_text('n_maps_multi', lang, n=config.MULTIVERSE.n_maps)
    else:
        n_maps = get_text('n_maps_single', lang)

    context = get_text(
        'run_config_text', lang,
        limit=f"{config.TEMPO_LIMITE:.1f}",
        n_maps=n_maps,
        start=config.START_NODE,
        goal=config.GOAL_NODE,
    )
    story.append(Paragraph(context, styles['body']))
    story.append(Spacer(1, 0.3 * cm))

    # table
    story.append(_build_results_table(results, styles, lang))
    story.append(Spacer(1, 0.6 * cm))

    # chart
    chart = _build_chart_reportlab(results, W - 2 * margin)
    if chart is not None:
        story.append(chart)
        story.append(Spacer(1, 0.6 * cm))

    # conclusion
    story.append(Paragraph(_build_conclusion(results, lang), styles['conclusion']))

    # ── build ──────────────────────────────────────────────────────────────────
    try:
        doc.build(story)
        messagebox.showinfo(
            get_text('export_success_title', lang),
            get_text('export_success_message', lang, path=path))
    except Exception as e:
        messagebox.showerror(get_text('export_error_title', lang), str(e))