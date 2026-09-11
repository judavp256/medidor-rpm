import io
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def generar_imagen_fft(f_plot, espectro_plot, f_1x, amp_1x, f_rot, n_armonicos, titulo, color_linea='#1f77b4'):
    """Genera una imagen PNG en memoria del gráfico FFT para incrustar en el PDF."""
    fig, ax = plt.subplots(figsize=(6.5, 2.8), dpi=150)
    ax.plot(f_plot, espectro_plot, color=color_linea, linewidth=1.2, label='Espectro FFT')
    
    # Marcar armónicos teóricos
    for n in range(1, n_armonicos + 1):
        f_arm = f_rot * n
        if f_arm <= f_plot[-1]:
            ax.axvline(x=f_arm, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
            ax.text(f_arm, ax.get_ylim()[1] * 0.9, f'{n}X', color='gray', fontsize=8, ha='center')
            
    # Marcar pico detectado si existe
    if f_1x is not None and amp_1x is not None:
        ax.plot(f_1x, amp_1x, 'rx', markersize=7, markeredgewidth=1.8, label=f'1X ({f_1x:.1f} Hz)')
        ax.annotate(f'{f_1x:.1f} Hz\n({f_1x*60:.0f} RPM)', 
                    (f_1x, amp_1x),
                    textcoords="offset points", 
                    xytext=(0, 7), 
                    ha='center', 
                    fontsize=8, 
                    fontweight='bold',
                    color='darkred')
                    
    ax.set_title(titulo, fontsize=10, fontweight='bold', pad=6)
    ax.set_xlabel('Frecuencia [Hz]', fontsize=8)
    ax.set_ylabel('Amplitud [m/s²]', fontsize=8)
    ax.set_xlim(0, f_plot[-1])
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper right', fontsize=7)
    plt.tight_layout()
    
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', bbox_inches='tight')
    plt.close(fig)
    img_buf.seek(0)
    return img_buf

def generar_codigo_latex(metadatos, parametros, resultados_base, rpm_promedio, rpm_std, rms_promedio, resultado_carga):
    """Genera el código fuente LaTeX (.tex) estructurado según el Formato IT."""
    fecha_actual = metadatos.get('fecha', datetime.date.today().strftime('%d/%m/%Y'))
    
    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{geometry}
\geometry{top=2cm, bottom=2cm, left=2.2cm, right=2.2cm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{tabularx}
\usepackage{fancyhdr}
\usepackage{hyperref}

\definecolor{primary}{RGB}{30, 58, 138}
\definecolor{lightgray}{RGB}{245, 247, 250}

\pagestyle{fancy}
\fancyhf{}
\rhead{\small \textbf{INFORME TÉCNICO} - MEDICIÓN DE RPM}
\lhead{\small """ + metadatos.get('proyecto', 'Ensayo de Vibración') + r"""}
\rfoot{\small Página \thepage}

\begin{document}

\begin{center}
    {\LARGE \textbf{\textcolor{primary}{INFORME TÉCNICO}}}\\[0.2cm]
    {\large \textbf{ANÁLISIS DE VIBRACIONES Y DETERMINACIÓN DE RPM POR FFT}}\\[0.1cm]
    {\small Fecha de emisión: """ + fecha_actual + r"""}
\end{center}

\vspace{0.3cm}

\section*{DESCRIPCIÓN DE LA INICIATIVA}
\begin{table}[h!]
\centering
\small
\begin{tabularx}{\textwidth}{|l|X|l|X|}
\hline
\textbf{Proyecto:} & """ + metadatos.get('proyecto', 'N/A') + r""" & \textbf{Fecha:} & """ + fecha_actual + r""" \\
\hline
\textbf{Categoría:} & """ + metadatos.get('categoria', 'Electrodomésticos') + r""" & \textbf{Tipo Proyecto:} & """ + metadatos.get('tipo_proyecto', 'Portafolio') + r""" \\
\hline
\textbf{Referencia:} & """ + metadatos.get('referencia', 'N/A') + r""" & \textbf{Centro de Costo:} & """ + metadatos.get('centro_costo', 'N/A') + r""" \\
\hline
\textbf{Estado:} & """ + metadatos.get('estado', 'Completado') + r""" & \textbf{Avance:} & """ + metadatos.get('avance', '100%') + r""" \\
\hline
\end{tabularx}
\end{table}

\textbf{Objetivo del Ensayo:} """ + metadatos.get('objetivo', 'Determinar con precisión las RPM de rotación mediante acelerómetro y análisis espectral.') + r"""

\section{Aspectos Preliminares}
El presente informe documenta la medición de velocidad de rotación mediante análisis de vibraciones acelerométricas. El objetivo es identificar la componente fundamental rotacional (1X) y descartar ruidos externos y resonancias mediante pruebas de coherencia y variación de carga.

\section{Procedimientos Realizados}
Se conectó un sensor acelerómetro uniaxial/triaxial al equipo bajo prueba. Se realizaron mediciones en dos condiciones operativas:
\begin{enumerate}
    \item \textbf{Condición Base / Vacío:} Registro de vibración a velocidad estable de operación sin carga aplicada.
    \item \textbf{Prueba de Confirmación con Carga / Frenado:} Registro aplicando una carga mecánica controlada (ej. agua o frenado) para verificar la variación y caída de la frecuencia fundamental de giro.
\end{enumerate}

\section{Detalles Técnicos del Sistema de Medición}
\begin{itemize}
    \item \textbf{Frecuencia de Muestreo ($F_s$):} """ + f"{parametros.get('fs', 11628)} Hz" + r"""
    \item \textbf{RPM Nominal de Placa:} """ + f"{parametros.get('rpm_nominal', 1750):.0f} RPM ({parametros.get('rpm_nominal', 1750)/60.0:.2f} Hz)" + r"""
    \item \textbf{Rango de Frecuencias Analizado:} 0 a """ + f"{parametros.get('freqplot', 200)} Hz" + r"""
    \item \textbf{Tolerancia Armónicos:} $\pm$""" + f"{parametros.get('tolerancia_hz', 1.5)} Hz" + r"""
\end{itemize}

\section{Resultados Obtenidos}

\begin{table}[h!]
\centering
\small
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Ensayo} & \textbf{Frecuencia 1X [Hz]} & \textbf{RPM Medida} & \textbf{Amplitud 1X} & \textbf{RMS [m/s²]} \\
\hline
"""
    for idx, r in enumerate(resultados_base):
        f_str = f"{r['f_1x']:.2f}" if r.get('f_1x') else "--"
        rpm_str = f"{r['rpm']:.1f}" if r.get('rpm') else "No detectado"
        amp_str = f"{r['amp_1x']:.4f}" if r.get('amp_1x') else "--"
        rms_str = f"{r['rms']:.4f}"
        tex += f"Ensayo {idx+1} (Vacío) & {f_str} & {rpm_str} & {amp_str} & {rms_str} \\\\\n\\hline\n"
        
    if resultado_carga and resultado_carga.get('f_carga'):
        tex += f"Con Carga (Validación) & {resultado_carga['f_carga']:.2f} & {resultado_carga['rpm_carga']:.1f} & {resultado_carga.get('amp_carga', 0.0):.4f} & {resultado_carga['rms']:.4f} \\\\\n\\hline\n"

    rpm_prom_str = f"{rpm_promedio:.1f} RPM" if rpm_promedio else "N/A"
    std_str = f"$\\pm${rpm_std:.2f} RPM" if rpm_std else "0.0 RPM"
    tex += r"""\end{tabular}
\caption{Resumen comparativo de mediciones adquiridas.}
\end{table}

\textbf{RPM Promedio en Vacío:} """ + rpm_prom_str + r""" (Dispersión: """ + std_str + r""") \\
\textbf{Vibración Global Promedio (RMS):} """ + f"{rms_promedio:.4f} m/s²" + r"""

\section{Validación con Carga}
"""
    if resultado_carga and resultado_carga.get('rpm_carga') and rpm_promedio:
        caida = rpm_promedio - resultado_carga['rpm_carga']
        pct = (caida / rpm_promedio) * 100.0
        tex += r"""Al someter el equipo a carga, la frecuencia de rotación se redujo de """ + f"{rpm_promedio:.1f}" + r""" RPM a """ + f"{resultado_carga['rpm_carga']:.1f}" + r""" RPM (reducción de """ + f"{caida:.1f}" + r""" RPM / """ + f"{pct:.1f}" + r"""\%). Esto confirma inequívocamente que la señal registrada obedece a la rotación del rotor y no a una perturbación de frecuencia fija."""
    else:
        tex += r"""No se aplicó ensayo con carga en esta prueba o no se registró desplazamiento significativo."""

    tex += r"""

\section{Conclusiones}
""" + metadatos.get('conclusiones', 'La velocidad de giro del equipo se encuentra dentro de los parámetros esperados de operación.') + r"""

\section{Observaciones}
""" + metadatos.get('observaciones', 'Ninguna observación adicional.') + r"""

\vspace{1.5cm}

\section*{Responsables}
\begin{center}
\begin{tabularx}{\textwidth}{X c X c X}
\cline{1-1} \cline{3-3} \cline{5-5}
\centering \textbf{Realizó:} """ + metadatos.get('responsable_realizo', 'Técnico de Campo') + r""" & & \centering \textbf{Revisó:} """ + metadatos.get('responsable_reviso', 'Ingeniero Responsable') + r""" & & \centering \textbf{Aprobó:} """ + metadatos.get('responsable_aprobo', 'Líder de Área') + r""" \\
\centering Fecha: """ + fecha_actual + r""" & & \centering Fecha: """ + fecha_actual + r""" & & \centering Fecha: """ + fecha_actual + r""" \\
\end{tabularx}
\end{center}

\end{document}
"""
    return tex

def generar_pdf_reportlab(metadatos, parametros, resultados_base, rpm_promedio, rpm_std, rms_promedio, resultado_carga, imagenes_bytes):
    """Genera el documento PDF formal siguiendo el Formato_IT_NUEVO.docx usando reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f2444'),
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#555555'),
        alignment=1
    )
    
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0f2444'),
        spaceBefore=10,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#222222')
    )
    
    bold_style = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#111111')
    )
    
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10
    )
    
    story = []
    
    # 1. Encabezado institucional
    story.append(Paragraph("INFORME TÉCNICO", title_style))
    story.append(Paragraph("ANÁLISIS DE VIBRACIONES Y MEDICIÓN DE RPM POR FFT", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f2444'), spaceBefore=0, spaceAfter=8))
    
    # 2. Tabla de Metadatos (DESCRIPCIÓN DE LA INICIATIVA - Formato_IT_NUEVO)
    fecha_actual = metadatos.get('fecha', datetime.date.today().strftime('%d/%m/%Y'))
    
    meta_data = [
        [Paragraph("<b>Proyecto:</b>", table_cell), Paragraph(metadatos.get('proyecto', 'N/A'), table_cell),
         Paragraph("<b>Fecha:</b>", table_cell), Paragraph(fecha_actual, table_cell)],
        [Paragraph("<b>Categoría:</b>", table_cell), Paragraph(metadatos.get('categoria', 'Refrigeración / Electrodomésticos'), table_cell),
         Paragraph("<b>Tipo Proyecto:</b>", table_cell), Paragraph(metadatos.get('tipo_proyecto', 'Portafolio'), table_cell)],
        [Paragraph("<b>Referencia:</b>", table_cell), Paragraph(metadatos.get('referencia', 'N/A'), table_cell),
         Paragraph("<b>Centro Costo:</b>", table_cell), Paragraph(metadatos.get('centro_costo', 'N/A'), table_cell)],
        [Paragraph("<b>Estado:</b>", table_cell), Paragraph(metadatos.get('estado', 'Completado'), table_cell),
         Paragraph("<b>Avance:</b>", table_cell), Paragraph(metadatos.get('avance', '100%'), table_cell)]
    ]
    
    meta_table = Table(meta_data, colWidths=[80, 190, 80, 190])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cccccc')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))
    
    # Objetivo
    story.append(Paragraph(f"<b>Objetivo:</b> {metadatos.get('objetivo', 'Medición y validación de RPM mediante análisis espectral de vibraciones.')}", body_style))
    story.append(Spacer(1, 10))
    
    # 3. Secciones Técnicas
    story.append(Paragraph("1. Aspectos Preliminares", h1_style))
    story.append(Paragraph("Se realizó la caracterización dinámica de vibraciones del artefacto con el propósito de determinar la velocidad angular de régimen (RPM) a través de la Transformada Rápida de Fourier (FFT), aislando componentes mecánicas de perturbaciones electromagnéticas o armónicas.", body_style))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("2. Procedimientos y Parámetros del Ensayo", h1_style))
    param_text = (
        f"• <b>Frecuencia de Muestreo (Fs):</b> {parametros.get('fs', 11628)} Hz &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"• <b>RPM Nominal de Placa:</b> {parametros.get('rpm_nominal', 1750):.0f} RPM ({parametros.get('rpm_nominal', 1750)/60.0:.2f} Hz)<br/>"
        f"• <b>Rango de Frecuencias:</b> 0 a {parametros.get('freqplot', 200)} Hz &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"• <b>Tolerancia Armónicos:</b> ±{parametros.get('tolerancia_hz', 1.5)} Hz"
    )
    story.append(Paragraph(param_text, body_style))
    story.append(Spacer(1, 8))
    
    # 4. Tabla de Resultados Obtenidos
    story.append(Paragraph("3. Resultados Obtenidos", h1_style))
    
    res_rows = [[
        Paragraph("<b>Ensayo / Condición</b>", table_cell_bold),
        Paragraph("<b>Nombre Archivo</b>", table_cell_bold),
        Paragraph("<b>Frec. 1X [Hz]</b>", table_cell_bold),
        Paragraph("<b>RPM Medida</b>", table_cell_bold),
        Paragraph("<b>Amp. 1X</b>", table_cell_bold),
        Paragraph("<b>RMS [m/s²]</b>", table_cell_bold)
    ]]
    
    for idx, r in enumerate(resultados_base):
        f_str = f"{r['f_1x']:.2f}" if r.get('f_1x') else "--"
        rpm_str = f"{r['rpm']:.1f}" if r.get('rpm') else "No detectado"
        amp_str = f"{r['amp_1x']:.4f}" if r.get('amp_1x') else "--"
        res_rows.append([
            Paragraph(f"Ensayo {idx+1} (Vacío)", table_cell),
            Paragraph(r['nombre'], table_cell),
            Paragraph(f_str, table_cell),
            Paragraph(f"<b>{rpm_str}</b>", table_cell),
            Paragraph(amp_str, table_cell),
            Paragraph(f"{r['rms']:.4f}", table_cell)
        ])
        
    if resultado_carga and resultado_carga.get('f_carga'):
        res_rows.append([
            Paragraph("<b>Con Carga (Validación)</b>", table_cell),
            Paragraph(resultado_carga['nombre'], table_cell),
            Paragraph(f"{resultado_carga['f_carga']:.2f}", table_cell),
            Paragraph(f"<b>{resultado_carga['rpm_carga']:.1f}</b>", table_cell),
            Paragraph(f"{resultado_carga.get('amp_carga', 0.0):.4f}", table_cell),
            Paragraph(f"{resultado_carga['rms']:.4f}", table_cell)
        ])
        
    res_table = Table(res_rows, colWidths=[100, 140, 75, 75, 75, 75])
    res_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fbfbfb')])
    ]))
    for i in range(len(res_rows[0])):
        res_table.setStyle(TableStyle([
            ('TEXTCOLOR', (i, 0), (i, 0), colors.white)
        ]))
    story.append(res_table)
    story.append(Spacer(1, 6))
    
    # Resumen de estadísticas
    rpm_p_str = f"{rpm_promedio:.1f} RPM" if rpm_promedio else "No determinado"
    std_p_str = f"± {rpm_std:.2f} RPM" if rpm_std else "0.0 RPM"
    stat_text = (
        f"<b>• RPM Promedio en Vacío:</b> <font color='#0f2444'><b>{rpm_p_str}</b></font> "
        f"(Dispersión: {std_p_str}) &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>• Vibración Global Promedio:</b> {rms_promedio:.4f} m/s² RMS"
    )
    story.append(Paragraph(stat_text, body_style))
    story.append(Spacer(1, 8))
    
    # 5. Validación con Carga
    story.append(Paragraph("4. Validación Operativa con Carga / Frenado", h1_style))
    if resultado_carga and resultado_carga.get('rpm_carga') and rpm_promedio:
        caida = rpm_promedio - resultado_carga['rpm_carga']
        pct = (caida / rpm_promedio) * 100.0
        val_text = (
            f"<b>✅ VALIDACIÓN EXITOSA:</b> Al someter el artefacto a condición de carga (ej. agua en licuadora o freno ligero), "
            f"la velocidad descendió de <b>{rpm_promedio:.1f} RPM</b> a <b>{resultado_carga['rpm_carga']:.1f} RPM</b> "
            f"(desplazamiento de -{caida:.1f} RPM / -{pct:.1f}%). "
            f"Esto ratifica con certeza física que el pico fundamental seleccionado pertenece al régimen de giro del eje mecánico, "
            f"descartando componentes electromagnéticas de red (60 Hz) o resonancias modales fijas."
        )
    else:
        val_text = "<i>No se adjuntó ensayo con carga o la variación de frecuencia no superó el umbral requerido.</i>"
    story.append(Paragraph(val_text, body_style))
    story.append(Spacer(1, 8))
    
    # 6. Gráficos FFT Incrustados
    if imagenes_bytes:
        story.append(Paragraph("5. Espectros de Frecuencia (Transformadas FFT)", h1_style))
        for titulo_img, img_data in imagenes_bytes:
            story.append(Paragraph(f"<b>{titulo_img}</b>", table_cell_bold))
            story.append(Spacer(1, 2))
            story.append(Image(img_data, width=520, height=200))
            story.append(Spacer(1, 6))
            
    # 7. Conclusiones y Observaciones
    story.append(Paragraph("6. Conclusiones", h1_style))
    concl = metadatos.get('conclusiones', f"Se determinó que la velocidad de rotación en vacío del artefacto es de {rpm_p_str}. La dispersión entre ensayos demostró alta repetibilidad operacional.")
    story.append(Paragraph(concl, body_style))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("7. Observaciones", h1_style))
    obs = metadatos.get('observaciones', "Se recomienda mantener los niveles de vibración monitoreados de acuerdo con la norma de producto correspondiente.")
    story.append(Paragraph(obs, body_style))
    story.append(Spacer(1, 14))
    
    # 8. Responsables y Firmas (Formato_IT_NUEVO)
    story.append(KeepTogether([
        Paragraph("8. Responsables del Ensayo", h1_style),
        Spacer(1, 15),
        Table([
            [
                Paragraph(f"____________________________<br/><b>Realizó:</b><br/>{metadatos.get('responsable_realizo', 'Técnico de Ensayos')}<br/>{fecha_actual}", table_cell),
                Paragraph(f"____________________________<br/><b>Revisó:</b><br/>{metadatos.get('responsable_reviso', 'Ingeniero Responsable')}<br/>{fecha_actual}", table_cell),
                Paragraph(f"____________________________<br/><b>Aprobó:</b><br/>{metadatos.get('responsable_aprobo', 'Líder Técnico')}<br/>{fecha_actual}", table_cell)
            ]
        ], colWidths=[180, 180, 180], style=[
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0)
        ])
    ]))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
