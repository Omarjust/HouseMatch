"""
Generador de PDF para el informe CMA usando ReportLab.
Instalar: pip install reportlab
"""
import io
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# Paleta de colores HouseMatch
AZUL = colors.HexColor('#1E3A5F')
AZUL_CLARO = colors.HexColor('#2E86AB')
VERDE = colors.HexColor('#27AE60')
GRIS_CLARO = colors.HexColor('#F5F7FA')
GRIS_BORDE = colors.HexColor('#D1D5DB')
NARANJA = colors.HexColor('#E67E22')


def _styles():
    base = getSampleStyleSheet()
    return {
        'titulo': ParagraphStyle('titulo', fontSize=22, textColor=AZUL,
                                  spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'subtitulo': ParagraphStyle('subtitulo', fontSize=11, textColor=AZUL_CLARO,
                                     spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica'),
        'seccion': ParagraphStyle('seccion', fontSize=13, textColor=AZUL,
                                   spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'),
        'normal': ParagraphStyle('normal', fontSize=10, leading=14, fontName='Helvetica'),
        'pequeño': ParagraphStyle('pequeño', fontSize=9, textColor=colors.grey, fontName='Helvetica'),
        'precio': ParagraphStyle('precio', fontSize=18, textColor=VERDE,
                                  alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'rango': ParagraphStyle('rango', fontSize=11, textColor=AZUL,
                                 alignment=TA_CENTER, fontName='Helvetica'),
    }


def _fmt_usd(value) -> str:
    try:
        return f"${float(value):,.0f} USD"
    except Exception:
        return str(value)


def generar_pdf_cma(analisis) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    st = _styles()
    story = []
    resultado = analisis.resultado_json or {}

    # ── ENCABEZADO ──────────────────────────────────────────────────────────
    story.append(Paragraph("ANÁLISIS COMPARATIVO DE MERCADO", st['titulo']))
    story.append(Paragraph("HouseMatch · Informe generado por IA", st['subtitulo']))
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL_CLARO, spaceAfter=10))

    # ── DATOS DE LA PROPIEDAD OBJETIVO ──────────────────────────────────────
    story.append(Paragraph("Propiedad a valuar", st['seccion']))

    obj_data = [
        ['Campo', 'Valor'],
        ['Título', analisis.obj_titulo],
        ['Cuartos', str(analisis.obj_cant_cuartos)],
        ['Baños', str(analisis.obj_cant_banios)],
        ['Área construida', f"{analisis.obj_area_construida} m²"],
        ['Área terreno', f"{analisis.obj_area_terreno} m²"],
        ['Estacionamiento', 'Sí' if analisis.obj_parqueo else 'No'],
        ['Piscina', 'Sí' if analisis.obj_piscina else 'No'],
        ['Antigüedad (1-5)', str(analisis.obj_antiguedad)],
        ['Zona / Ciudad', f"{analisis.obj_zona} · {analisis.obj_ciudad}"],
    ]

    t_obj = Table(obj_data, colWidths=[2.2 * inch, 4.8 * inch])
    t_obj.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [GRIS_CLARO, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_obj)
    story.append(Spacer(1, 12))

    # ── COMPARABLES ─────────────────────────────────────────────────────────
    story.append(Paragraph("Propiedades Comparables", st['seccion']))

    comps = [analisis.comparable_1, analisis.comparable_2, analisis.comparable_3]
    precio_m2_list = resultado.get('precio_m2_comparables', [])

    comp_header = ['', 'Comparable 1', 'Comparable 2', 'Comparable 3']
    comp_rows = [
        ['Título'] + [c.titulo[:30] for c in comps],
        ['Precio USD'] + [_fmt_usd(c.precio_usd) for c in comps],
        ['Cuartos'] + [str(c.cant_cuartos) for c in comps],
        ['Baños'] + [str(c.cant_banios) for c in comps],
        ['Área const.'] + [f"{c.area_construida} m²" for c in comps],
        ['Área terreno'] + [f"{c.area_terreno} m²" for c in comps],
        ['Estacionam.'] + ['Sí' if c.parqueo else 'No' for c in comps],
        ['Piscina'] + ['Sí' if c.piscina else 'No' for c in comps],
        ['Precio/m²'] + [
            _fmt_usd(next((x['precio_m2'] for x in precio_m2_list if x['comparable'] == i + 1), '—'))
            for i in range(3)
        ],
    ]

    t_comp = Table([comp_header] + comp_rows, colWidths=[1.5 * inch, 1.9 * inch, 1.9 * inch, 1.9 * inch])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_CLARO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [GRIS_CLARO, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 12))

    # ── PONDERACIÓN ─────────────────────────────────────────────────────────
    ponderacion = resultado.get('ponderacion', [])
    if ponderacion:
        story.append(Paragraph("Ponderación de Comparables", st['seccion']))
        pond_data = [['Comparable', 'Peso (%)', 'Justificación']]
        for p in ponderacion:
            pond_data.append([
                f"Comp. {p.get('comparable', '')}",
                f"{p.get('peso_pct', '')}%",
                p.get('razon', ''),
            ])
        t_pond = Table(pond_data, colWidths=[1.2 * inch, 1.2 * inch, 4.8 * inch])
        t_pond.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [GRIS_CLARO, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, GRIS_BORDE),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        story.append(t_pond)
        story.append(Spacer(1, 12))

    # ── AJUSTES ─────────────────────────────────────────────────────────────
    ajustes = resultado.get('ajustes', [])
    if ajustes:
        story.append(Paragraph("Ajustes Aplicados", st['seccion']))
        ajust_data = [['Comparable', 'Detalle de ajuste']]
        for a in ajustes:
            ajust_data.append([f"Comp. {a.get('comparable', '')}", a.get('detalle', '')])
        t_aj = Table(ajust_data, colWidths=[1.2 * inch, 6.0 * inch])
        t_aj.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [GRIS_CLARO, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, GRIS_BORDE),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_aj)
        story.append(Spacer(1, 14))

    # ── VALOR ESTIMADO (caja destacada) ─────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_CLARO, spaceAfter=8))
    story.append(Paragraph("💰 VALOR ESTIMADO DE LA PROPIEDAD", st['seccion']))

    precio_data = [
        ['Precio mínimo', 'Precio sugerido de lista', 'Precio máximo'],
        [
            _fmt_usd(analisis.precio_minimo),
            _fmt_usd(analisis.precio_sugerido),
            _fmt_usd(analisis.precio_maximo),
        ],
    ]
    t_precio = Table(precio_data, colWidths=[2.3 * inch, 2.6 * inch, 2.3 * inch])
    t_precio.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRIS_CLARO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('TEXTCOLOR', (0, 1), (0, 1), NARANJA),
        ('TEXTCOLOR', (1, 1), (1, 1), VERDE),
        ('TEXTCOLOR', (2, 1), (2, 1), NARANJA),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, AZUL_CLARO),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_precio)
    story.append(Spacer(1, 14))

    # ── JUSTIFICACIÓN ───────────────────────────────────────────────────────
    if analisis.justificacion:
        story.append(Paragraph("Justificación Ejecutiva", st['seccion']))
        story.append(Paragraph(analisis.justificacion, st['normal']))
        story.append(Spacer(1, 10))

    # ── CONSIDERACIONES ─────────────────────────────────────────────────────
    consideraciones = resultado.get('consideraciones', '')
    if consideraciones:
        story.append(Paragraph("⚠️ Consideraciones para el Agente", st['seccion']))
        story.append(Paragraph(consideraciones, st['normal']))
        story.append(Spacer(1, 10))

    # ── PIE DE PÁGINA ───────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=GRIS_BORDE, spaceBefore=14))
    story.append(Paragraph(
        f"Informe generado automáticamente por HouseMatch IA · "
        f"{analisis.creado_en.strftime('%d/%m/%Y %H:%M')} · "
        f"Este análisis no reemplaza un avalúo formal.",
        st['pequeño']
    ))

    doc.build(story)
    return buffer.getvalue()