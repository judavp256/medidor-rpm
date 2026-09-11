import io
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


# ─────────────────────────────────────────────────────────────────
# Utilidades de gráficos (matplotlib → PNG en memoria)
# ─────────────────────────────────────────────────────────────────
_COLORS = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2']

def generar_imagen_fft(f_plot, espectro_plot, f_1x, amp_1x, f_rot,
                       n_armonicos, titulo, color_linea='#1f77b4'):
    """Genera PNG en memoria del espectro FFT de un ensayo."""
    fig, ax = plt.subplots(figsize=(7.5, 2.8), dpi=150)
    ax.plot(f_plot, espectro_plot, color=color_linea, linewidth=1.2)

    # Armónicos
    for n in range(1, n_armonicos + 1):
        fa = f_rot * n
        if fa <= f_plot[-1]:
            ax.axvline(x=fa, color='#888888', linestyle='--', linewidth=0.8, alpha=0.6)
            ax.text(fa + 0.5, ax.get_ylim()[1] * 0.88,
                    f'{n}X', color='#666666', fontsize=7)

    # Pico detectado
    if f_1x is not None and amp_1x is not None:
        ax.plot(f_1x, amp_1x, 'rx', markersize=8, markeredgewidth=2)
        ax.annotate(f'{f_1x:.1f} Hz\n{f_1x*60:.0f} RPM',
                    xy=(f_1x, amp_1x),
                    xytext=(8, 6), textcoords='offset points',
                    fontsize=8, fontweight='bold', color='#c0392b')

    ax.set_title(titulo, fontsize=9.5, fontweight='bold', pad=5)
    ax.set_xlabel('Frecuencia [Hz]', fontsize=8)
    ax.set_ylabel('Amplitud [m/s²]', fontsize=8)
    ax.set_xlim(0, f_plot[-1])
    ax.grid(True, linestyle=':', alpha=0.45)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def generar_imagen_superposicion(ensayos, f_rot, n_armonicos):
    """Genera PNG con todos los espectros superpuestos."""
    fig, ax = plt.subplots(figsize=(7.5, 3.2), dpi=150)

    for idx, e in enumerate(ensayos):
        col = _COLORS[idx % len(_COLORS)]
        lbl = f"Medición {e['slot']}: {e.get('rpm') or e.get('rpm_carga') or 0:.0f} RPM"
        ls = '--' if e.get('tipo') == 'diferente' else '-'
        ax.plot(e['f_plot'], e['espectro_plot'],
                color=col, linewidth=1.2, linestyle=ls, label=lbl)

    # Armónicos
    if ensayos:
        fmax = ensayos[0]['f_plot'][-1]
        for n in range(1, n_armonicos + 1):
            fa = f_rot * n
            if fa <= fmax:
                ax.axvline(x=fa, color='#888888', linestyle=':', linewidth=0.8, alpha=0.6)

    ax.set_title('Superposición de Todos los Espectros FFT', fontsize=9.5, fontweight='bold')
    ax.set_xlabel('Frecuencia [Hz]', fontsize=8)
    ax.set_ylabel('Amplitud [m/s²]', fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.45)
    ax.legend(fontsize=7, loc='upper right')
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────
# Generador de código LaTeX
# ─────────────────────────────────────────────────────────────────
def generar_codigo_latex(meta, params, resultados, rpm_prom, rpm_std, rms_prom, res_dif):
    fecha = meta.get('fecha', datetime.date.today().strftime('%d/%m/%Y'))
    rpm_str = f"{rpm_prom:.1f} RPM" if rpm_prom else "No determinado"

    rows_latex = ""
    for idx, r in enumerate(resultados):
        f_str  = f"{r['f_1x']:.2f}"  if r.get('f_1x')  else "--"
        rp_str = f"{r['rpm']:.1f}"   if r.get('rpm')    else "No detectado"
        am_str = f"{r['amp_1x']:.4f}" if r.get('amp_1x') else "--"
        rows_latex += f"    Medición {idx+1} & {f_str} & {rp_str} & {am_str} & {r['rms']:.4f} \\\\\n    \\hline\n"

    if res_dif and res_dif.get('f_1x'):
        rows_latex += (f"    Medición 4 (Diferente) & {res_dif['f_1x']:.2f} & "
                       f"{res_dif.get('rpm',0):.1f} & {res_dif.get('amp_1x',0):.4f} & {res_dif['rms']:.4f} \\\\\n    \\hline\n")

    return (
        "\\documentclass[11pt,letterpaper]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[spanish]{babel}\n"
        "\\usepackage[top=2cm,bottom=2cm,left=2cm,right=2cm]{geometry}\n"
        "\\usepackage{booktabs,tabularx,xcolor,graphicx,fancyhdr}\n"
        "\\definecolor{primary}{RGB}{31,73,125}\n"
        "\\pagestyle{fancy}\n"
        "\\fancyhf{}\n"
        f"\\rhead{{\\small INFORME TÉCNICO - MEDICIÓN DE RPM}}\n"
        f"\\lhead{{\\small {meta.get('proyecto','')}}}\n"
        "\\rfoot{\\small Página \\thepage}\n"
        "\\begin{document}\n\n"
        "\\begin{center}\n"
        "{\\LARGE\\bfseries\\color{primary} INFORME TÉCNICO}\\\\[4pt]\n"
        "{\\large ANÁLISIS DE VIBRACIONES Y DETERMINACIÓN DE RPM}\\\\[2pt]\n"
        f"{{\\small Fecha: {fecha}}}\n"
        "\\end{center}\n\n"
        "\\section*{Descripción de la Iniciativa}\n"
        "\\begin{tabular}{|p{3cm}|p{4cm}|p{3cm}|p{4cm}|}\n"
        "\\hline\n"
        f"\\textbf{{Proyecto}} & {meta.get('proyecto','')} & \\textbf{{Fecha}} & {fecha}\\\\\n"
        "\\hline\n"
        f"\\textbf{{Módulo}} & {meta.get('modulo','')} & \\textbf{{Tipo Proyecto}} & {meta.get('tipo_proyecto','')}\\\\\n"
        "\\hline\n"
        f"\\textbf{{Referencia}} & {meta.get('referencia','')} & \\textbf{{Centro de Costo}} & {meta.get('centro_costo','')}\\\\\n"
        "\\hline\n"
        f"\\textbf{{Avance}} & {meta.get('avance','100\\%')} & \\textbf{{Estado}} & {meta.get('estado','')}\\\\\n"
        "\\hline\n"
        "\\end{tabular}\n\n"
        "\\medskip\n"
        "\\begin{tabular}{|p{3cm}|p{11.5cm}|}\n"
        "\\hline\n"
        f"\\textbf{{Objetivo}} & {meta.get('objetivo','')}\\\\\n"
        "\\hline\n"
        f"\\textbf{{Palabras clave}} & {meta.get('palabras_clave','Vibración, RPM, FFT, acelerómetro')}\\\\\n"
        "\\hline\n"
        "\\end{tabular}\n\n"
        "\\section{Aspectos Preliminares}\n"
        f"{meta.get('aspectos_preliminares', 'Se realizó la caracterización dinámica del equipo bajo análisis.')}\n\n"
        "\\section{Procedimientos Realizados}\n"
        "\\begin{tabular}{|l|c|c|}\n"
        "\\hline\n"
        "\\textbf{Prueba} & \\textbf{No cumple} & \\textbf{Cumple}\\\\\n"
        "\\hline\n"
        "Medición de vibración con acelerómetro & & X\\\\\n"
        "\\hline\n"
        "Análisis espectral FFT & & X\\\\\n"
        "\\hline\n"
        "\\end{tabular}\n\n"
        "\\section{Detalles Técnicos}\n"
        f"Frecuencia de Muestreo: {params.get('fs',11628)} Hz \\quad "
        f"RPM Nominal: {params.get('rpm_nominal',1750):.0f} \\quad "
        f"Rango visualización: 0-{params.get('freqplot',200)} Hz \\quad "
        f"Tolerancia: $\\pm${params.get('tolerancia_hz',1.5)} Hz\n\n"
        "\\section{Resultados Obtenidos}\n"
        "\\begin{tabular}{|l|c|c|c|c|}\n"
        "\\hline\n"
        "\\textbf{Ensayo} & \\textbf{Frec. 1X [Hz]} & \\textbf{RPM Medida} & \\textbf{Amplitud 1X} & \\textbf{RMS [m/s²]}\\\\\n"
        "\\hline\n"
        + rows_latex +
        "\\end{tabular}\n\n"
        f"\\textbf{{RPM Promedio (mediciones base):}} {rpm_str} \\quad "
        f"\\textbf{{Dispersión:}} $\\pm${rpm_std:.2f} RPM \\quad "
        f"\\textbf{{RMS Promedio:}} {rms_prom:.4f} m/s²\n\n"
        "\\section{Conclusiones}\n"
        f"{meta.get('conclusiones','Las mediciones se realizaron satisfactoriamente.')}\n\n"
        "\\section{Observaciones}\n"
        f"{meta.get('observaciones','Sin observaciones adicionales.')}\n\n"
        "\\section{Responsables}\n"
        "\\begin{center}\n"
        "\\begin{tabular}{p{4.5cm} p{4.5cm} p{4.5cm}}\n"
        "\\hline\n"
        f"\\centering\\textbf{{Realizó:}} {meta.get('responsable_realizo','')} & "
        f"\\centering\\textbf{{Revisó:}} {meta.get('responsable_reviso','')} & "
        f"\\centering\\textbf{{Aprobó:}} {meta.get('responsable_aprobo','')}\\\\\n"
        f"\\centering {fecha} & \\centering {fecha} & \\centering {fecha}\\\\\n"
        "\\end{tabular}\n"
        "\\end{center}\n\n"
        "\\end{document}\n"
    )


# ─────────────────────────────────────────────────────────────────
# Generador de PDF con ReportLab — estructura fiel al Formato_IT
# ─────────────────────────────────────────────────────────────────
def generar_pdf_reportlab(meta, params, resultados, rpm_prom, rpm_std,
                          rms_prom, res_dif, imagenes_bytes):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, KeepTogether, HRFlowable, PageBreak
    )

    # ── Colores del Formato_IT ──────────────────────────────────
    C_PRIMARY   = colors.HexColor('#1F497D')   # dk2 del tema
    C_ACCENT    = colors.HexColor('#4F81BD')   # accent1
    C_LABEL_BG  = colors.HexColor('#F2F2F2')   # fondo etiquetas tabla
    C_WHITE     = colors.white
    C_BORDER    = colors.HexColor('#BFBFBF')
    C_TEXT      = colors.HexColor('#1A1A1A')
    C_LIGHT_ROW = colors.HexColor('#F8F9FA')

    buf = io.BytesIO()
    # Carta con márgenes de 2 cm (≈ 1134 twips)
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    def sty(name, **kw):
        base = styles['Normal']
        return ParagraphStyle(name, parent=base, **kw)

    TIP_NOMBRE  = sty('TIP_NOMBRE',  fontName='Helvetica-Bold', fontSize=18,
                      textColor=C_PRIMARY, alignment=1, leading=22, spaceAfter=2)
    DESCR_STYLE = sty('DESCR',       fontName='Helvetica-Bold', fontSize=10,
                      textColor=C_PRIMARY, alignment=1, leading=14)
    H1          = sty('H1',          fontName='Helvetica-Bold', fontSize=12,
                      textColor=C_PRIMARY, leading=16, spaceBefore=10, spaceAfter=4)
    BODY        = sty('BODY',        fontName='Helvetica',      fontSize=9,
                      leading=13, textColor=C_TEXT)
    CELL_LBL    = sty('CELL_LBL',    fontName='Helvetica-Bold', fontSize=8,
                      leading=10, textColor=C_TEXT)
    CELL_VAL    = sty('CELL_VAL',    fontName='Helvetica',      fontSize=8,
                      leading=10, textColor=C_TEXT)
    TBL_HDR     = sty('TBL_HDR',     fontName='Helvetica-Bold', fontSize=8,
                      leading=10, textColor=C_WHITE)
    SIGN        = sty('SIGN',        fontName='Helvetica',      fontSize=8,
                      leading=12, alignment=1, textColor=C_TEXT)

    fecha = meta.get('fecha', datetime.date.today().strftime('%d/%m/%Y'))
    story = []

    # ── TABLA 0: Encabezado principal ────────────────────────────
    # Col0=logo (vacío) | Col1=título | Col2=Módulo: | Col3=valor módulo
    tbl0_data = [[
        Paragraph('', CELL_LBL),
        Paragraph('<b>INFORME TÉCNICO</b><br/>DESCRIPCIÓN DE LA INICIATIVA', DESCR_STYLE),
        Paragraph('<b>Módulo:</b>', CELL_LBL),
        Paragraph(meta.get('modulo', 'Producto / Portafolio'), CELL_VAL),
    ]]
    tbl0 = Table(tbl0_data, colWidths=[3.2*cm, 8.4*cm, 3.3*cm, 2.9*cm])
    tbl0.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.8, C_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, C_BORDER),
        ('BACKGROUND',    (2, 0), (2, 0),   C_LABEL_BG),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('LINEABOVE',     (0, 0), (-1, 0),  2, C_PRIMARY),
    ]))
    story.append(tbl0)
    story.append(Spacer(1, 6))

    # ── TABLA 1: Metadatos (4 filas × 6 col como en el Word) ─────
    # Fila 0: Categoría|Valor|Tipo proy.|Valor|Fecha|Valor
    # Fila 1: Proyecto |Valor(merged)|CentroCosto|Valor|Referencia|Valor
    # Fila 2: (row with values spanning)
    # Fila 3: Avance|Valor|Estado|Valor|Resultado|Valor
    tbl1_data = [
        [Paragraph('<b>Categoría de Producto</b>', CELL_LBL),
         Paragraph(meta.get('categoria', 'Refrigeración'), CELL_VAL),
         Paragraph('<b>Tipo de Proyecto</b>', CELL_LBL),
         Paragraph(meta.get('tipo_proyecto', 'Portafolio'), CELL_VAL),
         Paragraph('<b>Fecha</b>', CELL_LBL),
         Paragraph(fecha, CELL_VAL)],

        [Paragraph('<b>Proyecto</b>', CELL_LBL),
         Paragraph(meta.get('proyecto', ''), CELL_VAL),
         Paragraph('<b>Centro de Costo</b>', CELL_LBL),
         Paragraph(meta.get('centro_costo', ''), CELL_VAL),
         Paragraph('<b>Referencia</b>', CELL_LBL),
         Paragraph(meta.get('referencia', 'N/A'), CELL_VAL)],

        [Paragraph('<b>Avance</b>', CELL_LBL),
         Paragraph(meta.get('avance', '100%'), CELL_VAL),
         Paragraph('<b>Estado</b>', CELL_LBL),
         Paragraph(meta.get('estado', 'Completado'), CELL_VAL),
         Paragraph('<b>Resultado</b>', CELL_LBL),
         Paragraph('', CELL_VAL)],
    ]

    col_w1 = [3.0*cm, 3.5*cm, 3.0*cm, 3.5*cm, 2.0*cm, 2.8*cm]
    tbl1 = Table(tbl1_data, colWidths=col_w1)
    tbl1.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.8, C_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, C_BORDER),
        # Labels background
        ('BACKGROUND',    (0, 0), (0, -1), C_LABEL_BG),
        ('BACKGROUND',    (2, 0), (2, -1), C_LABEL_BG),
        ('BACKGROUND',    (4, 0), (4, -1), C_LABEL_BG),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tbl1)
    story.append(Spacer(1, 6))

    # ── TABLA 2: Objetivo + Palabras clave ───────────────────────
    tbl2_data = [
        [Paragraph('<b>Objetivo</b>', CELL_LBL),
         Paragraph(meta.get('objetivo', ''), CELL_VAL),
         Paragraph('<b>Palabras Clave</b>', CELL_LBL)],
        [Paragraph('', CELL_LBL),
         Paragraph('', CELL_VAL),
         Paragraph(meta.get('palabras_clave', 'Vibración, RPM, FFT, Acelerómetro'), CELL_VAL)],
    ]
    tbl2 = Table(tbl2_data, colWidths=[3.0*cm, 9.8*cm, 4.0*cm])
    tbl2.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.8, C_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, C_BORDER),
        ('BACKGROUND',    (0, 0), (0, -1), C_LABEL_BG),
        ('BACKGROUND',    (2, 0), (2, 0), C_LABEL_BG),
        ('SPAN',          (0, 0), (0, 1)),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tbl2)
    story.append(Spacer(1, 10))

    # ── TABLA CONTENIDO (índice simplificado) ────────────────────
    toc_items = [
        '1. Aspectos Preliminares',
        '2. Procedimientos Realizados',
        '3. Detalles Técnicos',
        '4. Resultados Obtenidos',
        '5. Conclusiones',
        '6. Observaciones',
        '7. Responsables',
    ]
    story.append(Paragraph('<b>Contenido</b>', H1))
    for item in toc_items:
        story.append(Paragraph(f'&nbsp;&nbsp;{item}', BODY))
    story.append(Spacer(1, 12))

    # ── SECCIÓN 1: Aspectos Preliminares ────────────────────────
    story.append(Paragraph('1. Aspectos Preliminares', H1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=4))
    story.append(Paragraph(meta.get('aspectos_preliminares',
        'Se realizó la caracterización dinámica de vibraciones del equipo bajo análisis '
        'para determinar la velocidad angular de régimen (RPM) mediante análisis espectral '
        'FFT a partir de señales de aceleración.'), BODY))
    story.append(Spacer(1, 8))

    # ── SECCIÓN 2: Procedimientos Realizados ────────────────────
    story.append(Paragraph('2. Procedimientos Realizados', H1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=4))

    tbl3_data = [
        [Paragraph('<b>Pruebas</b>', TBL_HDR),
         Paragraph('<b>No Cumple</b>', TBL_HDR),
         Paragraph('<b>Cumple</b>', TBL_HDR)],
        [Paragraph('Medición de vibración con acelerómetro', CELL_VAL),
         Paragraph('', CELL_VAL),
         Paragraph('X', CELL_LBL)],
        [Paragraph('Análisis espectral FFT', CELL_VAL),
         Paragraph('', CELL_VAL),
         Paragraph('X', CELL_LBL)],
    ]
    tbl3 = Table(tbl3_data, colWidths=[11*cm, 3*cm, 2.8*cm])
    tbl3.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), C_PRIMARY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
        ('BOX',           (0, 0), (-1, -1), 0.8, C_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [C_WHITE, C_LIGHT_ROW]),
    ]))
    story.append(tbl3)
    story.append(Spacer(1, 8))

    # ── SECCIÓN 3: Detalles Técnicos ────────────────────────────
    story.append(Paragraph('3. Detalles Técnicos', H1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=4))
    det_txt = (
        f"<b>Frecuencia de Muestreo (Fs):</b> {params.get('fs', 11628)} Hz &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>RPM Nominal de Placa:</b> {params.get('rpm_nominal', 1750):.0f} RPM "
        f"({params.get('rpm_nominal', 1750)/60.0:.2f} Hz)<br/>"
        f"<b>Rango de Frecuencias Analizado:</b> 0 a {params.get('freqplot', 200)} Hz &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Tolerancia Armónicos:</b> ±{params.get('tolerancia_hz', 1.5)} Hz"
    )
    story.append(Paragraph(det_txt, BODY))
    story.append(Spacer(1, 8))

    # ── SECCIÓN 4: Resultados Obtenidos ─────────────────────────
    story.append(Paragraph('4. Resultados Obtenidos', H1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=4))

    # Tabla de resultados por medición
    res_rows = [[
        Paragraph('<b>Medición</b>', TBL_HDR),
        Paragraph('<b>Nombre Archivo</b>', TBL_HDR),
        Paragraph('<b>Frec. 1X [Hz]</b>', TBL_HDR),
        Paragraph('<b>RPM Medida</b>', TBL_HDR),
        Paragraph('<b>Amp. 1X</b>', TBL_HDR),
        Paragraph('<b>RMS [m/s²]</b>', TBL_HDR),
    ]]

    for idx, r in enumerate(resultados):
        f_str  = f"{r['f_1x']:.2f}"   if r.get('f_1x')  else '—'
        rp_str = f"{r['rpm']:.1f}"    if r.get('rpm')    else 'No detectado'
        am_str = f"{r['amp_1x']:.4f}" if r.get('amp_1x') else '—'
        bg = C_WHITE if idx % 2 == 0 else C_LIGHT_ROW
        res_rows.append([
            Paragraph(f'Medición {idx+1}', CELL_VAL),
            Paragraph(r.get('nombre', ''), CELL_VAL),
            Paragraph(f_str,  CELL_VAL),
            Paragraph(f'<b>{rp_str}</b>', CELL_VAL),
            Paragraph(am_str, CELL_VAL),
            Paragraph(f"{r['rms']:.4f}", CELL_VAL),
        ])

    if res_dif and res_dif.get('f_1x'):
        idx_d = len(resultados)
        res_rows.append([
            Paragraph('<b>Medición 4 (Dif.)</b>', CELL_VAL),
            Paragraph(res_dif.get('nombre', ''), CELL_VAL),
            Paragraph(f"{res_dif['f_1x']:.2f}", CELL_VAL),
            Paragraph(f"<b>{res_dif.get('rpm', 0):.1f}</b>", CELL_VAL),
            Paragraph(f"{res_dif.get('amp_1x', 0):.4f}", CELL_VAL),
            Paragraph(f"{res_dif['rms']:.4f}", CELL_VAL),
        ])

    res_tbl = Table(res_rows, colWidths=[2.4*cm, 4.5*cm, 2.5*cm, 2.5*cm, 2.3*cm, 2.6*cm])
    res_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), C_PRIMARY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
        ('BOX',           (0, 0), (-1, -1), 0.8, C_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('ALIGN',         (2, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(res_tbl)
    story.append(Spacer(1, 6))

    rpm_p_str = f"{rpm_prom:.1f} RPM" if rpm_prom else "No determinado"
    story.append(Paragraph(
        f"<b>RPM Promedio (mediciones base):</b> <font color='#1F497D'><b>{rpm_p_str}</b></font> &nbsp;|&nbsp; "
        f"<b>Dispersión:</b> ±{rpm_std:.2f} RPM &nbsp;|&nbsp; "
        f"<b>RMS Promedio:</b> {rms_prom:.4f} m/s²", BODY))
    story.append(Spacer(1, 8))

    # Diagnóstico diferencia con Medición 4
    if res_dif and res_dif.get('rpm') and rpm_prom:
        delta = rpm_prom - res_dif['rpm']
        pct   = abs(delta / rpm_prom) * 100.0
        if delta > 0:
            diag = (f"<b>Diagnóstico:</b> La Medición 4 registró una velocidad de "
                    f"{res_dif['rpm']:.1f} RPM, es decir, <b>{delta:.1f} RPM ({pct:.1f}%) "
                    f"inferior</b> a las mediciones base. Esto confirma que el pico identificado "
                    f"corresponde a la rotación mecánica del eje y no a una frecuencia fija externa.")
        else:
            diag = (f"<b>Diagnóstico:</b> La Medición 4 registró {res_dif['rpm']:.1f} RPM. "
                    f"La variación respecto a las mediciones base fue de {abs(delta):.1f} RPM ({pct:.1f}%).")
        story.append(Paragraph(diag, BODY))
        story.append(Spacer(1, 6))

    # Gráficos incrustados
    if imagenes_bytes:
        story.append(Paragraph('<b>Gráficos de los Espectros FFT:</b>', BODY))
        story.append(Spacer(1, 4))
        for titulo_img, img_data in imagenes_bytes:
            story.append(Paragraph(f'<i>{titulo_img}</i>', CELL_VAL))
            story.append(Spacer(1, 2))
            story.append(Image(img_data, width=460, height=170))
            story.append(Spacer(1, 6))

    # ── SECCIÓN 5: Conclusiones ──────────────────────────────────
    story.append(Paragraph('5. Conclusiones', H1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=4))
    story.append(Paragraph(meta.get('conclusiones',
        f'La velocidad de rotación en condición base del equipo se determinó en {rpm_p_str}.'), BODY))
    story.append(Spacer(1, 8))

    # ── SECCIÓN 6: Observaciones ────────────────────────────────
    story.append(Paragraph('6. Observaciones', H1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=4))
    story.append(Paragraph(meta.get('observaciones',
        'Se recomienda realizar monitoreo periódico de los niveles de vibración global.'), BODY))
    story.append(Spacer(1, 14))

    # ── SECCIÓN 7: Responsables / Firmas ───────────────────────
    story.append(Paragraph('7. Responsables', H1))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_ACCENT, spaceAfter=10))

    sign_data = [[
        Paragraph(meta.get('responsable_realizo', ''), SIGN),
        Paragraph(meta.get('responsable_reviso', ''), SIGN),
        Paragraph(meta.get('responsable_aprobo', ''), SIGN),
    ], [
        Paragraph('—' * 34, SIGN),
        Paragraph('—' * 34, SIGN),
        Paragraph('—' * 34, SIGN),
    ], [
        Paragraph('<b>Realizó</b>', SIGN),
        Paragraph('<b>Revisó</b>',  SIGN),
        Paragraph('<b>Aprobó</b>',  SIGN),
    ], [
        Paragraph(fecha, SIGN),
        Paragraph(fecha, SIGN),
        Paragraph(fecha, SIGN),
    ]]
    sign_tbl = Table(sign_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    sign_tbl.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sign_tbl)

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────
# Generador de Word (.docx) — Fiel al Formato_IT_NUEVO.docx
# ─────────────────────────────────────────────────────────────────
def generar_docx(meta, params, resultados, rpm_prom, rpm_std,
                 rms_prom, res_dif, imagenes_bytes):
    """
    Genera un documento Word (.docx) con la estructura exacta del
    Formato_IT_NUEVO.docx: tablas de encabezado, metadatos, objetivo,
    secciones 1-7 y bloque de firmas.
    """
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    # ── Colores institucionales ───────────────────────────────────
    C_PRIMARY = RGBColor(0x1F, 0x49, 0x7D)
    C_WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
    HEX_PRIMARY = '1F497D'
    HEX_ACCENT  = '4F81BD'
    HEX_LABEL   = 'F2F2F2'
    HEX_LIGHT   = 'F8F9FA'
    HEX_AMBER   = 'FFF3CD'

    fecha = meta.get('fecha', datetime.date.today().strftime('%d/%m/%Y'))

    doc = Document()

    # ── Página: Carta, márgenes 2 cm ─────────────────────────────
    for sec in doc.sections:
        sec.page_width    = Cm(21.59)
        sec.page_height   = Cm(27.94)
        sec.left_margin   = Cm(2)
        sec.right_margin  = Cm(2)
        sec.top_margin    = Cm(2)
        sec.bottom_margin = Cm(2)

    # ── Fuente por defecto ────────────────────────────────────────
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(9)

    # ── Helpers ───────────────────────────────────────────────────
    def _shade(cell, hex_color):
        tc   = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd  = tcPr.find(qn('w:shd'))
        if shd is None:
            shd = OxmlElement('w:shd')
            tcPr.append(shd)
        shd.set(qn('w:val'),   'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'),  hex_color.lstrip('#'))

    def _ctext(cell, text, bold=False, color=None, size=8.5,
               align=WD_ALIGN_PARAGRAPH.LEFT):
        para = cell.paragraphs[0]
        para.clear()
        para.alignment = align
        para.paragraph_format.space_before = Pt(2)
        para.paragraph_format.space_after  = Pt(2)
        run = para.add_run(str(text))
        run.bold = bold
        run.font.size = Pt(size)
        run.font.name = 'Calibri'
        if color:
            run.font.color.rgb = color

    def _borders(table, color='BFBFBF'):
        tbl  = table._tbl
        tblP = tbl.find(qn('w:tblPr'))
        if tblP is None:
            tblP = OxmlElement('w:tblPr')
            tbl.insert(0, tblP)
        old = tblP.find(qn('w:tblBorders'))
        if old is not None:
            tblP.remove(old)
        brd = OxmlElement('w:tblBorders')
        for name in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            b = OxmlElement(f'w:{name}')
            b.set(qn('w:val'),   'single')
            b.set(qn('w:sz'),    '4')
            b.set(qn('w:space'), '0')
            b.set(qn('w:color'), color.lstrip('#'))
            brd.append(b)
        tblP.append(brd)

    def _h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after  = Pt(4)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = C_PRIMARY
        run.font.name = 'Calibri'
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bot  = OxmlElement('w:bottom')
        bot.set(qn('w:val'),   'single')
        bot.set(qn('w:sz'),    '6')
        bot.set(qn('w:space'), '1')
        bot.set(qn('w:color'), HEX_ACCENT)
        pBdr.append(bot)
        pPr.append(pBdr)

    def _body(text):
        p = doc.add_paragraph(str(text))
        for r in p.runs:
            r.font.size = Pt(9)
            r.font.name = 'Calibri'
        p.paragraph_format.space_after = Pt(4)

    def _spacer(pt=4):
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after  = Pt(pt)

    # ══════════════════════════════════════════════════════════════
    # TABLA 0: Encabezado (1 fila × 4 columnas) — Formato_IT Table 0
    # ══════════════════════════════════════════════════════════════
    tbl0 = doc.add_table(rows=1, cols=4)
    for i, w in enumerate([Cm(3.2), Cm(8.4), Cm(3.3), Cm(2.9)]):
        for cell in tbl0.columns[i].cells:
            cell.width = w

    r0 = tbl0.rows[0]

    # Col 0: espacio para logo
    _shade(r0.cells[0], HEX_LABEL)
    _ctext(r0.cells[0], '', size=8)

    # Col 1: Título institucional (fondo azul)
    _shade(r0.cells[1], HEX_PRIMARY)
    para1 = r0.cells[1].paragraphs[0]
    para1.clear()
    para1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para1.paragraph_format.space_before = Pt(6)
    para1.paragraph_format.space_after  = Pt(6)
    t1a = para1.add_run('INFORME TÉCNICO\n')
    t1a.bold = True; t1a.font.size = Pt(14)
    t1a.font.color.rgb = C_WHITE; t1a.font.name = 'Calibri'
    t1b = para1.add_run('DESCRIPCIÓN DE LA INICIATIVA')
    t1b.bold = False; t1b.font.size = Pt(9)
    t1b.font.color.rgb = C_WHITE; t1b.font.name = 'Calibri'

    # Col 2: Módulo label (fondo gris)
    _shade(r0.cells[2], HEX_LABEL)
    _ctext(r0.cells[2], 'Módulo:', bold=True, size=8)

    # Col 3: Módulo valor
    _ctext(r0.cells[3], meta.get('modulo', ''), size=8)

    _borders(tbl0)
    _spacer(3)

    # ══════════════════════════════════════════════════════════════
    # TABLA 1: Metadatos (3 filas × 6 columnas) — Formato_IT Table 1
    # ══════════════════════════════════════════════════════════════
    tbl1 = doc.add_table(rows=3, cols=6)
    for i, w in enumerate([Cm(3.0), Cm(3.5), Cm(3.0), Cm(3.5), Cm(2.0), Cm(2.8)]):
        for cell in tbl1.columns[i].cells:
            cell.width = w

    # Fila 0: Categoría | Val | Tipo Proy. | Val | Fecha | Val
    r = tbl1.rows[0]
    _shade(r.cells[0], HEX_LABEL); _ctext(r.cells[0], 'Categoría de Producto', bold=True, size=8)
    _ctext(r.cells[1], meta.get('categoria', 'Refrigeración'), size=8)
    _shade(r.cells[2], HEX_LABEL); _ctext(r.cells[2], 'Tipo de Proyecto', bold=True, size=8)
    _ctext(r.cells[3], meta.get('tipo_proyecto', 'Portafolio'), size=8)
    _shade(r.cells[4], HEX_LABEL); _ctext(r.cells[4], 'Fecha', bold=True, size=8)
    _ctext(r.cells[5], fecha, size=8)

    # Fila 1: Proyecto | Val | C.Costo | Val | Referencia | Val
    r = tbl1.rows[1]
    _shade(r.cells[0], HEX_LABEL); _ctext(r.cells[0], 'Proyecto', bold=True, size=8)
    _ctext(r.cells[1], meta.get('proyecto', ''), size=8)
    _shade(r.cells[2], HEX_LABEL); _ctext(r.cells[2], 'Centro de Costo', bold=True, size=8)
    _ctext(r.cells[3], meta.get('centro_costo', ''), size=8)
    _shade(r.cells[4], HEX_LABEL); _ctext(r.cells[4], 'Referencia', bold=True, size=8)
    _ctext(r.cells[5], meta.get('referencia', 'N/A'), size=8)

    # Fila 2: Avance | Val | Estado | Val | Resultado | Val
    r = tbl1.rows[2]
    _shade(r.cells[0], HEX_LABEL); _ctext(r.cells[0], 'Avance', bold=True, size=8)
    _ctext(r.cells[1], meta.get('avance', '100%'), size=8)
    _shade(r.cells[2], HEX_LABEL); _ctext(r.cells[2], 'Estado', bold=True, size=8)
    _ctext(r.cells[3], meta.get('estado', 'Completado'), size=8)
    _shade(r.cells[4], HEX_LABEL); _ctext(r.cells[4], 'Resultado', bold=True, size=8)
    _ctext(r.cells[5], '', size=8)

    _borders(tbl1)
    _spacer(3)

    # ══════════════════════════════════════════════════════════════
    # TABLA 2: Objetivo + Palabras clave (2 filas × 3 columnas) — Formato_IT Table 2
    # ══════════════════════════════════════════════════════════════
    tbl2 = doc.add_table(rows=2, cols=3)
    for i, w in enumerate([Cm(3.0), Cm(9.8), Cm(4.0)]):
        for cell in tbl2.columns[i].cells:
            cell.width = w

    tbl2.cell(0, 0).merge(tbl2.cell(1, 0))
    _shade(tbl2.cell(0, 0), HEX_LABEL)
    _ctext(tbl2.cell(0, 0), 'Objetivo', bold=True, size=8)
    _ctext(tbl2.cell(0, 1), meta.get('objetivo', ''), size=8)
    _shade(tbl2.cell(0, 2), HEX_LABEL)
    _ctext(tbl2.cell(0, 2), 'Palabras Clave', bold=True, size=8)
    _ctext(tbl2.cell(1, 2), meta.get('palabras_clave', 'Vibración, RPM, FFT, Acelerómetro'), size=8)

    _borders(tbl2)
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN 1: Aspectos Preliminares
    # ══════════════════════════════════════════════════════════════
    _h1('1. Aspectos Preliminares')
    _body(meta.get('aspectos_preliminares',
          'Se realizó la caracterización dinámica del equipo bajo análisis.'))

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN 2: Procedimientos Realizados (con tabla de Pruebas)
    # ══════════════════════════════════════════════════════════════
    _h1('2. Procedimientos Realizados')
    tbl3 = doc.add_table(rows=3, cols=3)
    for i, w in enumerate([Cm(11.0), Cm(3.0), Cm(2.8)]):
        for cell in tbl3.columns[i].cells:
            cell.width = w

    r = tbl3.rows[0]
    for i, lbl in enumerate(['Pruebas', 'No Cumple', 'Cumple']):
        _shade(r.cells[i], HEX_PRIMARY)
        _ctext(r.cells[i], lbl, bold=True, color=C_WHITE, size=8,
               align=WD_ALIGN_PARAGRAPH.CENTER)

    for idx, (prueba, nc, c) in enumerate([
        ('Medición de vibración con acelerómetro', '', 'X'),
        ('Análisis espectral FFT', '', 'X'),
    ]):
        r = tbl3.rows[idx + 1]
        if idx % 2 == 1:
            for cell in r.cells:
                _shade(cell, HEX_LIGHT)
        _ctext(r.cells[0], prueba, size=8)
        _ctext(r.cells[1], nc, size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _ctext(r.cells[2], c,  size=8, align=WD_ALIGN_PARAGRAPH.CENTER)

    _borders(tbl3)
    _spacer()

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN 3: Detalles Técnicos
    # ══════════════════════════════════════════════════════════════
    _h1('3. Detalles Técnicos')
    p_det = doc.add_paragraph()
    p_det.paragraph_format.space_after = Pt(4)
    for txt, bold in [
        ('Frecuencia de Muestreo (Fs): ', True),
        (f"{params.get('fs', 11628)} Hz     ", False),
        ('RPM Nominal de Placa: ', True),
        (f"{params.get('rpm_nominal', 1750):.0f} RPM  ({params.get('rpm_nominal', 1750)/60.0:.2f} Hz)\n", False),
        ('Rango de Frecuencias Analizado: ', True),
        (f"0 a {params.get('freqplot', 200)} Hz     ", False),
        ('Tolerancia Armónicos: ', True),
        (f"±{params.get('tolerancia_hz', 1.5)} Hz", False),
    ]:
        run = p_det.add_run(str(txt))
        run.bold = bold
        run.font.size = Pt(9)
        run.font.name = 'Calibri'
        if bold:
            run.font.color.rgb = C_PRIMARY

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN 4: Resultados Obtenidos
    # ══════════════════════════════════════════════════════════════
    _h1('4. Resultados Obtenidos')

    n_extra = 1 if (res_dif and res_dif.get('f_1x')) else 0
    tbl4 = doc.add_table(rows=1 + len(resultados) + n_extra, cols=6)
    for i, w in enumerate([Cm(2.4), Cm(4.5), Cm(2.5), Cm(2.5), Cm(2.3), Cm(2.6)]):
        for cell in tbl4.columns[i].cells:
            cell.width = w

    # Encabezado tabla resultados
    r = tbl4.rows[0]
    for i, lbl in enumerate(['Medición', 'Nombre Archivo', 'Frec. 1X [Hz]',
                              'RPM Medida', 'Amp. 1X', 'RMS [m/s²]']):
        _shade(r.cells[i], HEX_PRIMARY)
        _ctext(r.cells[i], lbl, bold=True, color=C_WHITE, size=8,
               align=WD_ALIGN_PARAGRAPH.CENTER)

    # Filas de datos
    for idx, res in enumerate(resultados):
        r = tbl4.rows[idx + 1]
        if idx % 2 == 1:
            for cell in r.cells:
                _shade(cell, HEX_LIGHT)
        f_str  = f"{res['f_1x']:.2f}"   if res.get('f_1x')  else '—'
        rp_str = f"{res['rpm']:.1f}"    if res.get('rpm')    else 'No detectado'
        am_str = f"{res['amp_1x']:.4f}" if res.get('amp_1x') else '—'
        vals   = [f'Medición {idx+1}', res.get('nombre', ''),
                  f_str, rp_str, am_str, f"{res['rms']:.4f}"]
        for i, v in enumerate(vals):
            align = WD_ALIGN_PARAGRAPH.CENTER if i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            _ctext(r.cells[i], v, bold=(i == 3 and bool(res.get('rpm'))),
                   size=8, align=align)

    # Fila medición diferente
    if res_dif and res_dif.get('f_1x'):
        r = tbl4.rows[-1]
        _shade(r.cells[0], HEX_AMBER)
        vals = ['Med. 4 (Diferente)', res_dif.get('nombre', ''),
                f"{res_dif['f_1x']:.2f}", f"{res_dif.get('rpm', 0):.1f}",
                f"{res_dif.get('amp_1x', 0):.4f}", f"{res_dif['rms']:.4f}"]
        for i, v in enumerate(vals):
            align = WD_ALIGN_PARAGRAPH.CENTER if i >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            _ctext(r.cells[i], v, bold=(i == 3), size=8, align=align)

    _borders(tbl4)

    # Resumen estadístico
    rpm_p_str = f"{rpm_prom:.1f} RPM" if rpm_prom else "No determinado"
    p_sum = doc.add_paragraph()
    p_sum.paragraph_format.space_before = Pt(6)
    p_sum.paragraph_format.space_after  = Pt(4)
    for txt, bold in [
        ('RPM Promedio (base): ', True),
        (f'{rpm_p_str}     ', False),
        ('Dispersión: ', True),
        (f'±{rpm_std:.2f} RPM     ', False),
        ('RMS Promedio: ', True),
        (f'{rms_prom:.4f} m/s²', False),
    ]:
        run = p_sum.add_run(str(txt))
        run.bold = bold
        run.font.size = Pt(9)
        run.font.name = 'Calibri'
        if bold:
            run.font.color.rgb = C_PRIMARY

    # Diagnóstico
    if res_dif and res_dif.get('rpm') and rpm_prom:
        delta = rpm_prom - res_dif['rpm']
        pct   = abs(delta / rpm_prom) * 100
        p_dx  = doc.add_paragraph()
        p_dx.paragraph_format.space_before = Pt(3)
        p_dx.paragraph_format.space_after  = Pt(4)
        r_lbl = p_dx.add_run('Diagnóstico: ')
        r_lbl.bold = True
        r_lbl.font.size = Pt(9)
        r_lbl.font.color.rgb = C_PRIMARY
        r_lbl.font.name = 'Calibri'
        txt_dx = (
            f"La Medición 4 registró {res_dif['rpm']:.1f} RPM, una reducción de "
            f"{delta:.1f} RPM ({pct:.1f}%) respecto a las mediciones base. "
            "Esto confirma que el pico corresponde a la rotación mecánica real del eje."
            if delta > 0 else
            f"La Medición 4 registró {res_dif['rpm']:.1f} RPM "
            f"(variación de {abs(delta):.1f} RPM, {pct:.1f}%)."
        )
        r_txt = p_dx.add_run(txt_dx)
        r_txt.font.size = Pt(9)
        r_txt.font.name = 'Calibri'

    # Imágenes embebidas de los gráficos
    if imagenes_bytes:
        sup_item = None
        for titulo_img, img_data in imagenes_bytes:
            if 'Superposición' in titulo_img:
                sup_item = (titulo_img, img_data)
                continue
            _spacer(4)
            p_lbl = doc.add_paragraph()
            p_lbl.paragraph_format.space_before = Pt(6)
            r_lbl = p_lbl.add_run(titulo_img)
            r_lbl.italic = True
            r_lbl.font.size = Pt(8.5)
            r_lbl.font.color.rgb = C_PRIMARY
            r_lbl.font.name = 'Calibri'
            img_data.seek(0)
            doc.add_picture(img_data, width=Cm(16.5))
            _spacer(3)

        if sup_item:
            _spacer(4)
            p_lbl = doc.add_paragraph()
            p_lbl.paragraph_format.space_before = Pt(6)
            r_lbl = p_lbl.add_run(sup_item[0])
            r_lbl.italic = True
            r_lbl.font.size = Pt(8.5)
            r_lbl.font.color.rgb = C_PRIMARY
            r_lbl.font.name = 'Calibri'
            sup_item[1].seek(0)
            doc.add_picture(sup_item[1], width=Cm(16.5))

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN 5: Conclusiones
    # ══════════════════════════════════════════════════════════════
    _h1('5. Conclusiones')
    _body(meta.get('conclusiones',
          f'La velocidad de rotación en condición base se determinó en {rpm_p_str}.'))

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN 6: Observaciones
    # ══════════════════════════════════════════════════════════════
    _h1('6. Observaciones')
    _body(meta.get('observaciones',
          'Se recomienda realizar monitoreo periódico de los niveles de vibración global.'))

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN 7: Responsables (tabla de firmas — 3 columnas)
    # ══════════════════════════════════════════════════════════════
    _h1('7. Responsables')
    _spacer(8)

    tbl_s = doc.add_table(rows=4, cols=3)
    for col in tbl_s.columns:
        for cell in col.cells:
            cell.width = Cm(5.8)

    sign_rows = [
        [meta.get('responsable_realizo', ''),
         meta.get('responsable_reviso', ''),
         meta.get('responsable_aprobo', '')],
        ['─' * 30, '─' * 30, '─' * 30],
        ['Realizó', 'Revisó', 'Aprobó'],
        [fecha, fecha, fecha],
    ]
    sign_bold = [False, False, True, False]

    for ri, row_data in enumerate(sign_rows):
        r = tbl_s.rows[ri]
        for ci, txt in enumerate(row_data):
            _ctext(r.cells[ci], txt, bold=sign_bold[ri], size=8.5,
                   align=WD_ALIGN_PARAGRAPH.CENTER)

    # ── Guardar en BytesIO ────────────────────────────────────────
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()
