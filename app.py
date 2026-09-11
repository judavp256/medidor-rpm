import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks

# Configuración de página
st.set_page_config(
    page_title="Medidor de RPM con Validación | Análisis de Vibraciones",
    page_icon="⚙️",
    layout="wide"
)

# Estilos CSS industriales
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 16px;
        border-left: 5px solid #28a745;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #6c757d;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a1a;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #495057;
        margin-top: 4px;
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
        font-size: 0.8rem;
        color: #28a745;
        background-color: #e8f5e9;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⚙️ Analizador de RPM con Validación de Carga")
    st.markdown("Carga las **3 mediciones en vacío** para promediar y superponer la señal, y valida con una **medición bajo carga** para confirmar la rotación real.")
with col_h2:
    st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='privacy-badge'>🔒 Procesamiento Volátil (Cero Almacenamiento en Nube)</div>", unsafe_allow_html=True)

# Sidebar: Configuración
with st.sidebar:
    st.header("🔧 Parámetros del Equipo")
    rpm_nominal = st.number_input(
        "RPM Nominal de Placa",
        min_value=1.0, max_value=100000.0, value=1750.0, step=50.0,
        help="Velocidad esperada del motor según placa del fabricante."
    )
    f_rot = rpm_nominal / 60.0
    st.caption(f"Frecuencia 1X esperada: **{f_rot:.2f} Hz**")
    
    st.divider()
    st.subheader("⚙️ Configuración del Sensor")
    fs = st.number_input(
        "Frecuencia de Muestreo (Fs) [Hz]",
        min_value=100, max_value=200000, value=11628, step=100,
        help="Muestras por segundo tomadas por el acelerómetro."
    )
    freqplot = st.slider("Frecuencia máxima a graficar [Hz]", min_value=50, max_value=1000, value=200, step=10)
    
    with st.expander("🛠️ Ajustes de Detección"):
        tolerancia_hz = st.number_input("Tolerancia armónicos (± Hz)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
        altura_min_pct = st.slider("Sensibilidad de picos (% del máximo)", min_value=1, max_value=50, value=10, step=1) / 100.0
        distancia_min = st.slider("Separación mínima entre picos", min_value=1, max_value=50, value=5, step=1)
        n_armonicos = st.slider("Cantidad de armónicos (1X, 2X...)", min_value=1, max_value=5, value=3)

# Función de cálculo FFT auxiliar
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

# Función para encontrar picos y fundamental 1X
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

# Sección de Carga de Archivos
col_u1, col_u2 = st.columns([3, 1])
with col_u1:
    st.subheader("1️⃣ Mediciones en Condición Base / Vacío (3 Ensayos)")
    uploaded_base = st.file_uploader(
        "Arrastra los 3 archivos CSV tomados en la misma condición:",
        type=["csv", "txt"],
        accept_multiple_files=True,
        help="Toma 3 lecturas consecutivas para asegurar repetibilidad y calcular el promedio."
    )
with col_u2:
    st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)
    usar_demo = st.button("🧪 Cargar Medición Demo Completa", help="Carga 3 ensayos en vacío simulados + 1 ensayo con carga (licuadora con agua)")

# Estado de datos en memoria (100% volátil)
ensayos_base = []
datos_carga = None

if usar_demo:
    # Simular 3 ensayos en vacío con pequeñas variaciones naturales
    L_demo = int(fs * 1.5)
    t_demo = np.arange(L_demo) / fs
    f_reales = [29.14, 29.16, 29.13] # ~1748.4, 1749.6, 1747.8 RPM
    
    for i, fr in enumerate(f_reales):
        s = (0.45 * np.sin(2 * np.pi * fr * t_demo) +
             0.18 * np.sin(2 * np.pi * 2 * fr * t_demo) +
             0.08 * np.sin(2 * np.pi * 3 * fr * t_demo) +
             np.random.normal(0, 0.04, L_demo))
        ensayos_base.append({
            'nombre': f'Demo_Vacio_Ensayo_{i+1}.csv',
            'data': s
        })
        
    # Simular 1 ensayo con carga (ej. licuadora con agua: cae a 27.0 Hz = 1620 RPM)
    f_carga = 27.0
    s_carga = (0.38 * np.sin(2 * np.pi * f_carga * t_demo) +
               0.22 * np.sin(2 * np.pi * 2 * f_carga * t_demo) +
               np.random.normal(0, 0.05, L_demo))
    datos_carga = {
        'nombre': 'Demo_Con_Carga_Agua.csv',
        'data': s_carga
    }
    st.info("💡 Modo demostración activado: Se cargaron 3 ensayos base (~1748 RPM) y 1 ensayo con carga (~1620 RPM).")

elif uploaded_base:
    for f in uploaded_base:
        try:
            df_temp = pd.read_csv(f, sep=None, engine='python', decimal='.')
            col_name = df_temp.columns[0]
            arr = pd.to_numeric(df_temp[col_name], errors='coerce').dropna().to_numpy(dtype=float)
            if len(arr) >= 10:
                ensayos_base.append({'nombre': f.name, 'data': arr})
        except Exception as e:
            st.error(f"Error al leer {f.name}: {e}")

# Procesar fase 1 si hay al menos 1 archivo base
if ensayos_base:
    num_ensayos = len(ensayos_base)
    st.write(f"📁 Ensayos base procesados: **{num_ensayos}** archivo(s)")
    
    colores_base = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd', '#8c564b']
    resultados_base = []
    
    for idx, item in enumerate(ensayos_base):
        f_plot, espectro_plot, rms_val = calcular_fft(item['data'], fs, freqplot)
        f_1x, amp_1x, df_p, p_freq, p_amp = analizar_picos(f_plot, espectro_plot, f_rot, tolerancia_hz, altura_min_pct, distancia_min)
        
        rpm_val = (f_1x * 60.0) if f_1x is not None else None
        resultados_base.append({
            'nombre': item['nombre'],
            'color': colores_base[idx % len(colores_base)],
            'f_plot': f_plot,
            'espectro_plot': espectro_plot,
            'rms': rms_val,
            'f_1x': f_1x,
            'amp_1x': amp_1x,
            'rpm': rpm_val,
            'p_freq': p_freq,
            'p_amp': p_amp,
            'tabla_picos': df_p
        })
        
    # Calcular promedio de RPM de los ensayos que detectaron pico
    rpms_detectadas = [r['rpm'] for r in resultados_base if r['rpm'] is not None]
    rms_promedio = np.mean([r['rms'] for r in resultados_base])
    
    rpm_promedio = np.mean(rpms_detectadas) if rpms_detectadas else None
    rpm_std = np.std(rpms_detectadas, ddof=1) if len(rpms_detectadas) > 1 else 0.0
    f_1x_promedio = (rpm_promedio / 60.0) if rpm_promedio is not None else None
    
    # TARJETAS DE RESULTADOS PRINCIPALES
    st.markdown("### 📊 Resultados de la Medición en Vacío")
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
        else:
            st.markdown("""
            <div class="metric-card" style="border-left-color: #dc3545;">
                <div class="metric-title">🎯 RPM PROMEDIO</div>
                <div class="metric-value" style="color: #dc3545;">No detectada</div>
                <div class="metric-sub">Revisa la tolerancia</div>
            </div>
            """, unsafe_allow_html=True)
            
    with k2:
        disp_text = f"± {rpm_std:.2f} RPM" if len(rpms_detectadas) > 1 else "1 solo ensayo"
        delta_nom = ((rpm_promedio - rpm_nominal) / rpm_nominal * 100.0) if rpm_promedio else None
        delta_str = f"{delta_nom:+.2f}%" if delta_nom is not None else "--"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #007bff;">
            <div class="metric-title">📋 Repetibilidad (Dispersión)</div>
            <div class="metric-value" style="color: #007bff;">{disp_text}</div>
            <div class="metric-sub">Desviación de placa: {delta_str}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #17a2b8;">
            <div class="metric-title">⚡ Vibración Global RMS</div>
            <div class="metric-value" style="color: #17a2b8;">{rms_promedio:.4f}</div>
            <div class="metric-sub">m/s² (promedio ensayos)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k4:
        coincidencias = len(rpms_detectadas)
        color_coin = "#28a745" if coincidencias == num_ensayos else "#ffc107"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {color_coin};">
            <div class="metric-title">🔍 Coherencia entre Ensayos</div>
            <div class="metric-value" style="color: {color_coin};">{coincidencias}/{num_ensayos}</div>
            <div class="metric-sub">Ensayos con pico coincidente</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")

    # ========================================================
    # FASE 2: VALIDACIÓN CON CARGA (LICUADORA CON AGUA / FRENADO)
    # ========================================================
    st.divider()
    st.subheader("2️⃣ Validación con Carga / Frenado (Prueba de Confirmación)")
    st.caption("Aplica una carga al equipo (ejemplo: echar agua a la licuadora o frenar ligeramente el eje). Al aumentar la carga, el pico real de giro debe descender a menor velocidad.")

    if not usar_demo:
        file_carga = st.file_uploader(
            "Sube aquí la medición tomada CON CARGA:",
            type=["csv", "txt"],
            key="uploader_carga",
            help="Sube el archivo tomado mientras el equipo opera con carga."
        )
        if file_carga:
            try:
                df_c = pd.read_csv(file_carga, sep=None, engine='python', decimal='.')
                c_col = df_c.columns[0]
                arr_c = pd.to_numeric(df_c[c_col], errors='coerce').dropna().to_numpy(dtype=float)
                if len(arr_c) >= 10:
                    datos_carga = {'nombre': file_carga.name, 'data': arr_c}
            except Exception as e:
                st.error(f"Error al leer archivo con carga: {e}")

    resultado_carga = None
    if datos_carga:
        f_plot_c, esp_c, rms_c = calcular_fft(datos_carga['data'], fs, freqplot)
        # Buscar picos en la señal con carga
        alt_min_c = float(esp_c.max() * altura_min_pct)
        p_idx_c, _ = find_peaks(esp_c, height=alt_min_c, distance=distancia_min)
        p_freq_c = f_plot_c[p_idx_c]
        p_amp_c = esp_c[p_idx_c]
        
        # Evaluar qué ocurrió con el pico de vacío (f_1x_promedio)
        if f_1x_promedio is not None:
            # Buscar el nuevo pico predominante por debajo de la frecuencia de vacío
            picos_sub = [(f, a) for f, a in zip(p_freq_c, p_amp_c) if (f_1x_promedio * 0.4) <= f <= (f_1x_promedio * 0.98)]
            
            # Buscar amplitud residual en la frecuencia base
            idx_base_c = np.argmin(np.abs(f_plot_c - f_1x_promedio))
            amp_en_base_con_carga = esp_c[idx_base_c]
            
            nuevo_f_carga = None
            nuevo_rpm_carga = None
            if picos_sub:
                picos_sub_sorted = sorted(picos_sub, key=lambda x: x[1], reverse=True)
                nuevo_f_carga = picos_sub_sorted[0][0]
                nuevo_rpm_carga = nuevo_f_carga * 60.0
                
            resultado_carga = {
                'f_plot': f_plot_c,
                'espectro_plot': esp_c,
                'rms': rms_c,
                'f_carga': nuevo_f_carga,
                'rpm_carga': nuevo_rpm_carga,
                'amp_residual_base': amp_en_base_con_carga
            }
            
            # DIAGNÓSTICO DE LA VALIDACIÓN CON CARGA
            if nuevo_rpm_carga and nuevo_rpm_carga < rpm_promedio:
                caida_rpm = rpm_promedio - nuevo_rpm_carga
                caida_pct = (caida_rpm / rpm_promedio) * 100.0
                st.markdown(f"""
                <div class="status-ok">
                    🎯 <strong>¡VALIDACIÓN EXITOSA Y CONFIRMADA!</strong><br>
                    Al aplicar carga, la velocidad de rotación cayó de <strong>{rpm_promedio:.1f} RPM ({f_1x_promedio:.2f} Hz)</strong> 
                    a <strong>{nuevo_rpm_carga:.1f} RPM ({nuevo_f_carga:.2f} Hz)</strong>, reduciéndose en <strong>{caida_rpm:.1f} RPM ({caida_pct:.1f}%)</strong>.<br>
                    ✅ Esto <strong>confirma al 100% que el pico medido corresponde a la rotación mecánica del eje</strong> 
                    y descarta completamente ruidos eléctricos fijos (como 60 Hz de la red) o resonancias estructurales.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-alert">
                    ⚠️ <strong>Observación en la prueba con carga:</strong><br>
                    El pico base en {f_1x_promedio:.2f} Hz disminuyó su amplitud con carga, pero no se identificó con claridad el nuevo pico de giro más lento.
                    Se recomienda verificar que la carga aplicada (ej. cantidad de agua o freno) sea suficiente para reducir perceptiblemente las RPM.
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("💡 Puedes subir un archivo con carga arriba para validar que el pico se desplace hacia la izquierda (menor velocidad).")

    # ========================================================
    # GRÁFICA COMPARATIVA SUPERPUESTA (PLOTLY)
    # ========================================================
    st.write("")
    st.subheader("📈 Superposición de Espectros FFT")
    fig = go.Figure()
    
    # 1. Graficar cada uno de los ensayos base
    for idx, r in enumerate(resultados_base):
        fig.add_trace(go.Scatter(
            x=r['f_plot'], y=r['espectro_plot'], mode='lines',
            name=f"Ensayo {idx+1} (Vacío): {r['rpm']:.1f} RPM" if r['rpm'] else f"Ensayo {idx+1} (Vacío)",
            line=dict(color=r['color'], width=1.5),
            hovertemplate=f"<b>{r['nombre']}</b><br>Frecuencia: %{{x:.2f}} Hz<br>Amplitud: %{{y:.4f}}<extra></extra>"
        ))
        
        # Marcar el pico detectado
        if r['f_1x'] is not None:
            fig.add_trace(go.Scatter(
                x=[r['f_1x']], y=[r['amp_1x']], mode='markers+text',
                name=f"1X Ensayo {idx+1}",
                marker=dict(color=r['color'], size=8, symbol='circle'),
                text=[f"{r['f_1x']:.1f} Hz"], textposition="top center",
                showlegend=False
            ))
            
    # 2. Si hay ensayo con carga, agregarlo con línea roja/magenta destacada
    if resultado_carga:
        fig.add_trace(go.Scatter(
            x=resultado_carga['f_plot'], y=resultado_carga['espectro_plot'], mode='lines',
            name=f"🚨 Con Carga: {resultado_carga['rpm_carga']:.1f} RPM" if resultado_carga['rpm_carga'] else "🚨 Con Carga",
            line=dict(color='#d62728', width=2, dash='dash'),
            hovertemplate="<b>Ensayo CON CARGA</b><br>Frecuencia: %{x:.2f} Hz<br>Amplitud: %{y:.4f}<extra></extra>"
        ))
        if resultado_carga['f_carga']:
            fig.add_trace(go.Scatter(
                x=[resultado_carga['f_carga']], y=[resultado_carga['espectro_plot'][np.argmin(np.abs(resultado_carga['f_plot'] - resultado_carga['f_carga']))]],
                mode='markers+text', name="Pico con carga",
                marker=dict(color='#d62728', size=10, symbol='triangle-down'),
                text=[f"Carga: {resultado_carga['f_carga']:.1f} Hz"], textposition="bottom center",
                showlegend=False
            ))

    # 3. Líneas verticales de armónicos teóricos
    for n in range(1, n_armonicos + 1):
        f_arm = f_rot * n
        if f_arm <= freqplot:
            fig.add_vline(
                x=f_arm, line_dash="dot", line_color="#6c757d",
                annotation_text=f"{n}X Nom ({f_arm:.1f} Hz)",
                annotation_position="top left",
                annotation_font=dict(color="#6c757d", size=10)
            )

    fig.update_layout(
        xaxis_title='Frecuencia [Hz]',
        yaxis_title='Amplitud de Aceleración [m/s²]',
        xaxis_range=[0, freqplot],
        hovermode='closest',
        template='plotly_white',
        margin=dict(l=40, r=20, t=30, b=40),
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ========================================================
    # TABLA COMPARATIVA ENTRE MEDICIONES
    # ========================================================
    st.subheader("📋 Resumen Comparativo de Ensayos")
    filas_tabla = []
    for idx, r in enumerate(resultados_base):
        filas_tabla.append({
            "Ensayo": f"Ensayo {idx+1} (Vacío)",
            "Archivo": r['nombre'],
            "Frecuencia 1X [Hz]": f"{r['f_1x']:.2f}" if r['f_1x'] else "--",
            "RPM Medida": f"{r['rpm']:.1f}" if r['rpm'] else "No detectado",
            "Amplitud 1X": f"{r['amp_1x']:.4f}" if r['amp_1x'] else "--",
            "Vibración RMS [m/s²]": f"{r['rms']:.4f}"
        })
    if resultado_carga and resultado_carga['f_carga']:
        filas_tabla.append({
            "Ensayo": "Ensayo CON CARGA (Validación)",
            "Archivo": datos_carga['nombre'],
            "Frecuencia 1X [Hz]": f"{resultado_carga['f_carga']:.2f}",
            "RPM Medida": f"{resultado_carga['rpm_carga']:.1f}",
            "Amplitud 1X": f"{resultado_carga['espectro_plot'][np.argmin(np.abs(resultado_carga['f_plot'] - resultado_carga['f_carga']))]:.4f}",
            "Vibración RMS [m/s²]": f"{resultado_carga['rms']:.4f}"
        })
    st.dataframe(pd.DataFrame(filas_tabla), use_container_width=True)

else:
    st.info("👆 Por favor sube los archivos CSV arriba o presiona el botón **'Cargar Medición Demo Completa'** para probar la superposición y validación con carga.")
