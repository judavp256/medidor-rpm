import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks
import datetime

# Importar generador de informes (PDF y LaTeX)
try:
    from report_generator import generar_imagen_fft, generar_pdf_reportlab, generar_codigo_latex
    REPORTLAB_DISPONIBLE = True
except Exception as e:
    REPORTLAB_DISPONIBLE = False

# Configuración de página
st.set_page_config(
    page_title="Analizador de RPM con Informe Técnico",
    page_icon="⚙️",
    layout="wide"
)

# Estilos CSS industriales
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 14px;
        border-left: 5px solid #28a745;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-title {
        font-size: 0.8rem;
        color: #6c757d;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 2px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a1a;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #495057;
        margin-top: 2px;
    }
    .status-ok {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
        padding: 14px;
        border-radius: 8px;
        font-weight: 500;
    }
    .status-alert {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
        padding: 14px;
        border-radius: 8px;
        font-weight: 500;
    }
    .privacy-badge {
        font-size: 0.75rem;
        color: #155724;
        background-color: #d4edda;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
        font-weight: 600;
    }
    .slot-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. CONTROL DE ACCESO POR CONTRASEÑA
# =========================================================================
PASSWORD_DEFAULT = "tecnico2026"
# Se puede sobreescribir con st.secrets si existe
PASSWORD_SISTEMA = st.secrets.get("PASSWORD", PASSWORD_DEFAULT) if hasattr(st, "secrets") else PASSWORD_DEFAULT

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)
        st.markdown("### 🔒 Acceso al Medidor de RPM")
        st.markdown("Plataforma de análisis de vibraciones y cálculo de velocidad de giro.")
        
        clave_ingresada = st.text_input("Ingresa la contraseña de acceso:", type="password")
        if st.button("Ingresar a la Plataforma", use_container_width=True):
            if clave_ingresada == PASSWORD_SISTEMA:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta. Por favor contacta al administrador.")
        st.caption(f"💡 Contraseña predeterminada: `{PASSWORD_DEFAULT}` (editable en código o secrets)")
    st.stop()

# =========================================================================
# 2. INTERFAZ PRINCIPAL (AUTENTICADA)
# =========================================================================
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⚙️ Analizador de RPM por Vibración")
    st.markdown("Determinación de velocidad de giro con acelerómetro, validación con carga y generación de informe técnico.")
with col_h2:
    st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='privacy-badge'>🔒 Procesamiento Volátil (Cero Almacenamiento)</div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()

# Barra Lateral: Parámetros del Equipo y de Detección
with st.sidebar:
    st.header("🔧 Parámetros del Equipo")
    rpm_nominal = st.number_input(
        "RPM Nominal de Placa",
        min_value=1.0, max_value=100000.0, value=1750.0, step=50.0,
        help="Velocidad esperada del motor según placa."
    )
    f_rot = rpm_nominal / 60.0
    st.caption(f"Frecuencia 1X esperada: **{f_rot:.2f} Hz**")
    
    st.divider()
    st.subheader("🎛️ Rango de Frecuencias y Sensor")
    
    # CASILLA DE RANGO DE FRECUENCIAS (Predeterminadamente en 200 Hz como pidió el usuario)
    freqplot = st.number_input(
        "Frecuencia máxima de visualización [Hz]",
        min_value=10,
        max_value=5000,
        value=200,
        step=20,
        help="Límite superior del eje de frecuencias. Por defecto carga en 200 Hz (valor original del código)."
    )
    
    fs = st.number_input(
        "Frecuencia de Muestreo (Fs) [Hz]",
        min_value=100, max_value=200000, value=11628, step=100,
        help="Frecuencia del acelerómetro."
    )
    
    with st.expander("🛠️ Ajustes Avanzados de Picos"):
        tolerancia_hz = st.number_input("Tolerancia armónicos (± Hz)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
        altura_min_pct = st.slider("Sensibilidad de picos (% del máximo)", min_value=1, max_value=50, value=10, step=1) / 100.0
        distancia_min = st.slider("Separación mínima entre picos", min_value=1, max_value=50, value=5, step=1)
        n_armonicos = st.slider("Cantidad de armónicos (1X, 2X...)", min_value=1, max_value=5, value=3)

# Funciones de procesamiento FFT y picos
def calcular_fft(signal_array, sampling_rate, max_freq):
    L = len(signal_array)
    rms = float(np.std(signal_array, ddof=1))
    nfft = 2 ** int(np.ceil(np.log2(L)))
    f = sampling_rate / 2 * np.linspace(0, 1, nfft // 2 + 1)
    fft_vals = np.fft.fft(signal_array, nfft) / L
    espectro = 2 * np.abs(fft_vals[:nfft // 2 + 1])
    
    mask = f <= max_freq
    f_plot = f[mask]
    espectro_plot = espectro[mask]
    return f_plot, espectro_plot, rms

def analizar_picos(f_plot, espectro_plot, f_objetivo, tol, min_pct, dist_min):
    alt_min = float(espectro_plot.max() * min_pct)
    p_idx, _ = find_peaks(espectro_plot, height=alt_min, distance=dist_min)
    p_freq = f_plot[p_idx]
    p_amp = espectro_plot[p_idx]
    
    df_p = pd.DataFrame({'Frecuencia [Hz]': p_freq, 'Amplitud': p_amp})
    df_p = df_p.sort_values('Amplitud', ascending=False).reset_index(drop=True)
    
    cercanos = df_p[np.abs(df_p['Frecuencia [Hz]'] - f_objetivo) <= tol]
    if not cercanos.empty:
        best = cercanos.iloc[0]
        return best['Frecuencia [Hz]'], best['Amplitud'], df_p, p_freq, p_amp
    return None, None, df_p, p_freq, p_amp

# =========================================================================
# 3. SLOTS DE CARGA FLEXIBLES (NO RESTRICTIVOS: HASTA 4 ARCHIVOS)
# =========================================================================
st.subheader("📁 Carga de Archivos de Medición (Flexible - No Restrictivo)")
st.caption("Carga los archivos disponibles. Puedes cargar solo 1 en vacío y 1 con carga, o los que tengas a disposición.")

c_slot1, c_slot2, c_slot3, c_slot4 = st.columns(4)

with c_slot1:
    f1 = st.file_uploader("1️⃣ Vacío - Ensayo 1 (Base)", type=["csv", "txt"], key="file1")
with c_slot2:
    f2 = st.file_uploader("2️⃣ Vacío - Ensayo 2 (Opcional)", type=["csv", "txt"], key="file2")
with c_slot3:
    f3 = st.file_uploader("3️⃣ Vacío - Ensayo 3 (Opcional)", type=["csv", "txt"], key="file3")
with c_slot4:
    f4 = st.file_uploader("🚨 Con Carga / Frenado (Opcional)", type=["csv", "txt"], key="file4")

col_d1, col_d2 = st.columns([3, 1])
with col_d2:
    usar_demo = st.button("🧪 Cargar Medición Demo", help="Simula los 3 ensayos en vacío (~1748 RPM) y 1 con carga (~1620 RPM)")

# Lectura y preparación de datos
archivos_cargados = []

def parsear_csv(archivo):
    try:
        df_t = pd.read_csv(archivo, sep=None, engine='python', decimal='.')
        col = df_t.columns[0]
        arr = pd.to_numeric(df_t[col], errors='coerce').dropna().to_numpy(dtype=float)
        if len(arr) >= 10:
            return arr
    except Exception:
        pass
    return None

if usar_demo:
    L_demo = int(fs * 1.5)
    t_demo = np.arange(L_demo) / fs
    f_reales = [29.14, 29.16, 29.13]
    for i, fr in enumerate(f_reales):
        s = (0.45 * np.sin(2 * np.pi * fr * t_demo) +
             0.18 * np.sin(2 * np.pi * 2 * fr * t_demo) +
             0.08 * np.sin(2 * np.pi * 3 * fr * t_demo) +
             np.random.normal(0, 0.04, L_demo))
        archivos_cargados.append({
            'tipo': 'vacio',
            'slot': i + 1,
            'nombre': f'Demo_Vacio_Ensayo_{i+1}.csv',
            'data': s
        })
    # Con carga
    f_c = 27.0
    s_c = (0.38 * np.sin(2 * np.pi * f_c * t_demo) +
           0.22 * np.sin(2 * np.pi * 2 * f_c * t_demo) +
           np.random.normal(0, 0.05, L_demo))
    archivos_cargados.append({
        'tipo': 'carga',
        'slot': 4,
        'nombre': 'Demo_Con_Carga_Agua.csv',
        'data': s_c
    })
    st.info("💡 Modo Demostración activado con 4 ensayos simulados.")
else:
    if f1:
        d1 = parsear_csv(f1)
        if d1 is not None: archivos_cargados.append({'tipo': 'vacio', 'slot': 1, 'nombre': f1.name, 'data': d1})
    if f2:
        d2 = parsear_csv(f2)
        if d2 is not None: archivos_cargados.append({'tipo': 'vacio', 'slot': 2, 'nombre': f2.name, 'data': d2})
    if f3:
        d3 = parsear_csv(f3)
        if d3 is not None: archivos_cargados.append({'tipo': 'vacio', 'slot': 3, 'nombre': f3.name, 'data': d3})
    if f4:
        d4 = parsear_csv(f4)
        if d4 is not None: archivos_cargados.append({'tipo': 'carga', 'slot': 4, 'nombre': f4.name, 'data': d4})

# =========================================================================
# 4. PROCESAMIENTO Y RESULTADOS
# =========================================================================
if archivos_cargados:
    ensayos_base_res = []
    ensayo_carga_res = None
    imagenes_para_pdf = []
    
    colores = {'vacio': ['#1f77b4', '#00a8cc', '#2ca02c'], 'carga': '#d62728'}
    vacio_count = 0
    
    for item in archivos_cargados:
        f_plot, esp_plot, rms_val = calcular_fft(item['data'], fs, freqplot)
        f_1x, amp_1x, df_p, p_freq, p_amp = analizar_picos(f_plot, esp_plot, f_rot, tolerancia_hz, altura_min_pct, distancia_min)
        rpm_val = (f_1x * 60.0) if f_1x is not None else None
        
        if item['tipo'] == 'vacio':
            col = colores['vacio'][vacio_count % len(colores['vacio'])]
            vacio_count += 1
            res_obj = {
                'slot': item['slot'],
                'nombre': item['nombre'],
                'tipo': 'vacio',
                'color': col,
                'f_plot': f_plot,
                'espectro_plot': esp_plot,
                'rms': rms_val,
                'f_1x': f_1x,
                'amp_1x': amp_1x,
                'rpm': rpm_val,
                'p_freq': p_freq,
                'p_amp': p_amp
            }
            ensayos_base_res.append(res_obj)
            
            # Generar imagen para el informe
            if REPORTLAB_DISPONIBLE:
                img_buf = generar_imagen_fft(f_plot, esp_plot, f_1x, amp_1x, f_rot, n_armonicos, f"Slot {item['slot']} (Vacío): {item['nombre']}", col)
                imagenes_para_pdf.append((f"Slot {item['slot']} (Vacío) - {rpm_val:.1f} RPM" if rpm_val else f"Slot {item['slot']}", img_buf))
        else:
            # Ensayo con carga
            # Buscar el nuevo pico de rotación más lento
            nuevo_f_carga = None
            nuevo_rpm_carga = None
            nueva_amp_carga = None
            
            # Si hay al menos un ensayo en vacío, comparamos contra f_rot o f_1x
            f_ref = f_rot
            if ensayos_base_res and ensayos_base_res[0]['f_1x']:
                f_ref = ensayos_base_res[0]['f_1x']
                
            picos_sub = [(f, a) for f, a in zip(p_freq, p_amp) if (f_ref * 0.4) <= f <= (f_ref * 0.98)]
            if picos_sub:
                picos_sub_sorted = sorted(picos_sub, key=lambda x: x[1], reverse=True)
                nuevo_f_carga = picos_sub_sorted[0][0]
                nueva_amp_carga = picos_sub_sorted[0][1]
                nuevo_rpm_carga = nuevo_f_carga * 60.0
                
            ensayo_carga_res = {
                'slot': 4,
                'nombre': item['nombre'],
                'tipo': 'carga',
                'color': colores['carga'],
                'f_plot': f_plot,
                'espectro_plot': esp_plot,
                'rms': rms_val,
                'f_carga': nuevo_f_carga,
                'amp_carga': nueva_amp_carga,
                'rpm_carga': nuevo_rpm_carga,
                'p_freq': p_freq,
                'p_amp': p_amp
            }
            if REPORTLAB_DISPONIBLE:
                img_buf_c = generar_imagen_fft(f_plot, esp_plot, nuevo_f_carga, nueva_amp_carga, f_rot, n_armonicos, f"Slot 4 (Con Carga): {item['nombre']}", '#d62728')
                imagenes_para_pdf.append((f"Slot 4 (Con Carga) - {nuevo_rpm_carga:.1f} RPM" if nuevo_rpm_carga else "Slot 4 (Con Carga)", img_buf_c))

    # Promedios y estadísticas de vacío
    rpms_validas = [r['rpm'] for r in ensayos_base_res if r['rpm'] is not None]
    rpm_promedio = np.mean(rpms_validas) if rpms_validas else None
    rpm_std = np.std(rpms_validas, ddof=1) if len(rpms_validas) > 1 else 0.0
    f_1x_promedio = (rpm_promedio / 60.0) if rpm_promedio else None
    rms_promedio = np.mean([r['rms'] for r in ensayos_base_res]) if ensayos_base_res else (ensayo_carga_res['rms'] if ensayo_carga_res else 0.0)

    # Tarjetas KPI
    st.markdown("### 📊 Indicadores Clave de Medición")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        if rpm_promedio is not None:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #28a745;">
                <div class="metric-title">🎯 RPM PROMEDIO REAL</div>
                <div class="metric-value" style="color: #28a745;">{rpm_promedio:.1f}</div>
                <div class="metric-sub">Frecuencia: {f_1x_promedio:.2f} Hz</div>
            </div>
            """, unsafe_allow_html=True)
        elif ensayo_carga_res and ensayo_carga_res['rpm_carga']:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #ff7f0e;">
                <div class="metric-title">🎯 RPM CON CARGA</div>
                <div class="metric-value" style="color: #ff7f0e;">{ensayo_carga_res['rpm_carga']:.1f}</div>
                <div class="metric-sub">Sin ensayos en vacío</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card" style="border-left-color: #dc3545;">
                <div class="metric-title">🎯 RPM PROMEDIO</div>
                <div class="metric-value" style="color: #dc3545;">No detectada</div>
                <div class="metric-sub">Ajusta la tolerancia</div>
            </div>
            """, unsafe_allow_html=True)

    with k2:
        delta_str = f"{((rpm_promedio - rpm_nominal) / rpm_nominal * 100.0):+.2f}%" if rpm_promedio else "--"
        disp_str = f"± {rpm_std:.2f} RPM" if len(rpms_validas) > 1 else ("1 ensayo" if len(rpms_validas) == 1 else "--")
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #007bff;">
            <div class="metric-title">📋 Repetibilidad / Desviación</div>
            <div class="metric-value" style="color: #007bff;">{disp_str}</div>
            <div class="metric-sub">Desviación nominal: {delta_str}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #17a2b8;">
            <div class="metric-title">⚡ Vibración Global RMS</div>
            <div class="metric-value" style="color: #17a2b8;">{rms_promedio:.4f}</div>
            <div class="metric-sub">m/s²</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        total_cargados = len(archivos_cargados)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #6f42c1;">
            <div class="metric-title">📁 Ensayos Analizados</div>
            <div class="metric-value" style="color: #6f42c1;">{total_cargados} / 4</div>
            <div class="metric-sub">{len(ensayos_base_res)} vacío | {1 if ensayo_carga_res else 0} con carga</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Diagnóstico de Validación con Carga
    if ensayo_carga_res and ensayo_carga_res['rpm_carga'] and rpm_promedio:
        caida = rpm_promedio - ensayo_carga_res['rpm_carga']
        caida_pct = (caida / rpm_promedio) * 100.0
        if caida > 0:
            st.markdown(f"""
            <div class="status-ok">
                🎯 <strong>¡VALIDACIÓN DE ROTACIÓN EXITOSA Y CONFIRMADA!</strong><br>
                Al aplicar carga, la velocidad de rotación cayó de <strong>{rpm_promedio:.1f} RPM ({f_1x_promedio:.2f} Hz)</strong> 
                a <strong>{ensayo_carga_res['rpm_carga']:.1f} RPM ({ensayo_carga_res['f_carga']:.2f} Hz)</strong> 
                (reducción de <strong>{caida:.1f} RPM / {caida_pct:.1f}%</strong>).<br>
                ✅ Esto <strong>certifica que el punto medido es la velocidad real del eje</strong> y descarta frecuencias fijas de red (60 Hz) o resonancias mecánicas.
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # =========================================================================
    # 5. LOS 4 GRÁFICOS DE TRANSFORMADAS FFT INDIVIDUALES
    # =========================================================================
    st.subheader("📈 Gráficos de las Transformadas de Fourier (FFT) Individuales")
    st.caption(f"Mostrando el espectro de 0 a **{freqplot} Hz** para cada archivo cargado:")

    todos_los_ensayos = ensayos_base_res.copy()
    if ensayo_carga_res:
        todos_los_ensayos.append(ensayo_carga_res)

    # Cuadrícula 2x2 para los 4 gráficos
    grid_cols = st.columns(2)
    for idx, e in enumerate(todos_los_ensayos):
        col_idx = idx % 2
        with grid_cols[col_idx]:
            fig_ind = go.Figure()
            
            # Traza espectro
            nombre_label = f"Slot {e['slot']}: {e['nombre']}"
            fig_ind.add_trace(go.Scatter(
                x=e['f_plot'], y=e['espectro_plot'], mode='lines',
                line=dict(color=e['color'], width=1.5),
                name='Espectro FFT',
                hovertemplate='Frec: %{x:.2f} Hz<br>Amp: %{y:.4f}<extra></extra>'
            ))
            
            # Marcador de pico fundamental
            if e['tipo'] == 'vacio' and e['f_1x']:
                fig_ind.add_trace(go.Scatter(
                    x=[e['f_1x']], y=[e['amp_1x']], mode='markers+text',
                    marker=dict(color='red', size=8, symbol='x'),
                    text=[f"1X: {e['f_1x']:.1f} Hz\n({e['rpm']:.0f} RPM)"],
                    textposition='top center',
                    textfont=dict(size=10, color='darkred'),
                    name='Pico 1X'
                ))
            elif e['tipo'] == 'carga' and e['f_carga']:
                fig_ind.add_trace(go.Scatter(
                    x=[e['f_carga']], y=[e['amp_carga']], mode='markers+text',
                    marker=dict(color='darkred', size=9, symbol='triangle-down'),
                    text=[f"Carga: {e['f_carga']:.1f} Hz\n({e['rpm_carga']:.0f} RPM)"],
                    textposition='bottom center',
                    textfont=dict(size=10, color='darkred'),
                    name='Pico con Carga'
                ))
                
            # Líneas guía de armónicos
            for n in range(1, n_armonicos + 1):
                f_arm = f_rot * n
                if f_arm <= freqplot:
                    fig_ind.add_vline(
                        x=f_arm, line_dash="dot", line_color="#888888",
                        annotation_text=f"{n}X ({f_arm:.1f} Hz)",
                        annotation_position="top left",
                        annotation_font=dict(color="#666666", size=9)
                    )
            
            titulo_grafico = f"<b>Slot {e['slot']}</b> ({'Vacío' if e['tipo']=='vacio' else 'Con Carga'}) | "
            if e['tipo'] == 'vacio' and e['rpm']:
                titulo_grafico += f"<span style='color:{e['color']};'>{e['rpm']:.1f} RPM</span> | RMS: {e['rms']:.3f}"
            elif e['tipo'] == 'carga' and e['rpm_carga']:
                titulo_grafico += f"<span style='color:red;'>{e['rpm_carga']:.1f} RPM</span> | RMS: {e['rms']:.3f}"
            else:
                titulo_grafico += f"RMS: {e['rms']:.3f}"

            fig_ind.update_layout(
                title=dict(text=titulo_grafico, font=dict(size=12)),
                xaxis=dict(title='Frecuencia [Hz]', range=[0, freqplot]),
                yaxis=dict(title='Amplitud [m/s²]'),
                margin=dict(l=35, r=15, t=35, b=35),
                height=320,
                template='plotly_white',
                showlegend=False
            )
            st.plotly_chart(fig_ind, use_container_width=True)

    # Gráfica superpuesta comparativa
    with st.expander("📈 Ver Gráfico Comparativo Superpuesto"):
        fig_sup = go.Figure()
        for e in todos_los_ensayos:
            fig_sup.add_trace(go.Scatter(
                x=e['f_plot'], y=e['espectro_plot'], mode='lines',
                line=dict(color=e['color'], width=1.5, dash='dash' if e['tipo']=='carga' else 'solid'),
                name=f"Slot {e['slot']} ({'Carga' if e['tipo']=='carga' else 'Vacío'}): {e.get('rpm', e.get('rpm_carga', 0.0)):.1f} RPM",
                hovertemplate=f"<b>{e['nombre']}</b><br>Frec: %{{x:.2f}} Hz<br>Amp: %{{y:.4f}}<extra></extra>"
            ))
        fig_sup.update_layout(
            xaxis=dict(title='Frecuencia [Hz]', range=[0, freqplot]),
            yaxis=dict(title='Amplitud [m/s²]'),
            margin=dict(l=40, r=20, t=30, b=40),
            height=450,
            template='plotly_white',
            hovermode='closest'
        )
        st.plotly_chart(fig_sup, use_container_width=True)

    # =========================================================================
    # 6. GENERADOR DE INFORME TÉCNICO EN PDF Y LATEX
    # =========================================================================
    st.divider()
    st.subheader("📄 Generación de Informe Técnico Oficial (Formato_IT)")
    st.caption("Completa los datos del proyecto para emitir el informe formal en PDF o exportar el código fuente LaTeX:")

    with st.form("form_informe"):
        st.markdown("##### 📝 Metadatos de la Iniciativa (Formato Institucional)")
        c_inf1, c_inf2 = st.columns(2)
        with c_inf1:
            inf_proyecto = st.text_input("Proyecto / Iniciativa", value="Evaluación Operacional de RPM por Vibraciones")
            inf_categoria = st.text_input("Categoría de Producto", value="Refrigeración / Electrodomésticos")
            inf_tipo = st.text_input("Tipo de Proyecto", value="Portafolio")
            inf_centro_costo = st.text_input("Centro de Costo", value="Mantenimiento y Confiabilidad")
        with c_inf2:
            inf_referencia = st.text_input("Referencia / Modelo del Equipo", value="REF-EXP-01")
            inf_estado = st.selectbox("Estado del Ensayo", ["Completado", "En curso", "Aprobado"], index=0)
            inf_avance = st.text_input("Avance (%)", value="100%")
            inf_fecha = st.date_input("Fecha del Ensayo", value=datetime.date.today()).strftime("%d/%m/%Y")

        st.markdown("##### 🎯 Objetivos y Observaciones del Ensayo")
        inf_objetivo = st.text_area("Objetivo del Ensayo", value="Determinar con exactitud la velocidad angular de régimen (RPM) mediante análisis FFT de vibraciones y validar la ausencia de interferencias electromagnéticas mediante prueba bajo carga.", height=70)
        
        c_obs1, c_obs2 = st.columns(2)
        with c_obs1:
            inf_conclusiones = st.text_area("Conclusiones Técnicas", value=f"La velocidad de rotación en régimen vacío se determinó en {rpm_promedio:.1f} RPM." if rpm_promedio else "Medición ejecutada.", height=90)
        with c_obs2:
            inf_observaciones = st.text_area("Observaciones y Recomendaciones", value="El comportamiento vibratorio global RMS se mantiene dentro de los límites estables de operación.", height=90)

        st.markdown("##### ✍️ Responsables de la Medición")
        c_resp1, c_resp2, c_resp3 = st.columns(3)
        with c_resp1:
            inf_realizo = st.text_input("Realizó (Técnico)", value="Técnico de Ensayos")
        with c_resp2:
            inf_reviso = st.text_input("Revisó (Ingeniero)", value="Ing. Especialista Vibraciones")
        with c_resp3:
            inf_aprobo = st.text_input("Aprobó (Líder Técnico)", value="Director de Laboratorio / Calidad")

        btn_generar = st.form_submit_button("⚡ Compilar Informe Técnico", use_container_width=True)

    if btn_generar or "informe_compilado" in st.session_state:
        st.session_state["informe_compilado"] = True
        
        metadatos_doc = {
            'proyecto': inf_proyecto,
            'categoria': inf_categoria,
            'tipo_proyecto': inf_tipo,
            'centro_costo': inf_centro_costo,
            'referencia': inf_referencia,
            'estado': inf_estado,
            'avance': inf_avance,
            'fecha': inf_fecha,
            'objetivo': inf_objetivo,
            'conclusiones': inf_conclusiones,
            'observaciones': inf_observaciones,
            'responsable_realizo': inf_realizo,
            'responsable_reviso': inf_reviso,
            'responsable_aprobo': inf_aprobo
        }
        
        parametros_doc = {
            'rpm_nominal': rpm_nominal,
            'fs': fs,
            'freqplot': freqplot,
            'tolerancia_hz': tolerancia_hz
        }
        
        col_down1, col_down2 = st.columns(2)
        
        # 1. Generar PDF con ReportLab
        if REPORTLAB_DISPONIBLE:
            try:
                pdf_bytes = generar_pdf_reportlab(
                    metadatos_doc, parametros_doc,
                    ensayos_base_res, rpm_promedio, rpm_std, rms_promedio,
                    ensayo_carga_res, imagenes_para_pdf
                )
                with col_down1:
                    st.download_button(
                        label="📥 Descargar Informe Técnico Oficial (.PDF)",
                        data=pdf_bytes,
                        file_name=f"Informe_Tecnico_RPM_{inf_referencia}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                with col_down1:
                    st.error(f"Error al generar PDF: {e}")
        else:
            with col_down1:
                st.warning("Instala 'reportlab' para generar el PDF automáticamente.")
                
        # 2. Generar código LaTeX (.tex)
        try:
            tex_content = generar_codigo_latex(
                metadatos_doc, parametros_doc,
                ensayos_base_res, rpm_promedio, rpm_std, rms_promedio,
                ensayo_carga_res
            )
            with col_down2:
                st.download_button(
                    label="📥 Descargar Código Fuente (.TEX / LaTeX)",
                    data=tex_content,
                    file_name=f"Informe_Tecnico_RPM_{inf_referencia}.tex",
                    mime="text/plain",
                    use_container_width=True
                )
        except Exception as e:
            with col_down2:
                st.error(f"Error al generar LaTeX: {e}")

else:
    st.info("👆 Por favor sube al menos un archivo CSV en los slots superiores o haz clic en **'Cargar Medición Demo'** para procesar los datos.")
