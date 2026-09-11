import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks

# Configuración de página
st.set_page_config(
    page_title="Medidor de RPM | Análisis de Vibraciones",
    page_icon="⚙️",
    layout="wide"
)

# Estilos CSS personalizados para una apariencia industrial y amigable
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
        padding: 12px;
        border-radius: 8px;
        font-weight: 500;
    }
    .status-alert {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
        padding: 12px;
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal
st.title("⚙️ Analizador de RPM por Vibración")
st.markdown("Herramienta simplificada para técnicos: carga el archivo CSV del acelerómetro para calcular automáticamente las **RPM reales** del equipo.")

# Sidebar: Configuración y parámetros
with st.sidebar:
    st.header("🔧 Parámetros de Medición")
    
    rpm_nominal = st.number_input(
        "RPM Nominal del Artefacto",
        min_value=1.0,
        max_value=100000.0,
        value=1750.0,
        step=50.0,
        help="Velocidad de rotación esperada de la placa del motor o equipo."
    )
    f_rot = rpm_nominal / 60.0
    st.caption(f"Frecuencia rotacional esperada (1X): **{f_rot:.2f} Hz**")
    
    st.divider()
    st.subheader("⚙️ Configuración del Sensor")
    
    fs = st.number_input(
        "Frecuencia de Muestreo (Fs) [Hz]",
        min_value=100,
        max_value=200000,
        value=11628,
        step=100,
        help="Frecuencia a la que el acelerómetro tomó las muestras."
    )
    
    freqplot = st.slider(
        "Frecuencia máxima a graficar [Hz]",
        min_value=50,
        max_value=1000,
        value=200,
        step=10
    )
    
    with st.expander("🛠️ Ajustes Avanzados de Detección"):
        tolerancia_hz = st.number_input("Tolerancia armónicos (± Hz)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
        altura_min_pct = st.slider("Sensibilidad de picos (% del máximo)", min_value=1, max_value=50, value=10, step=1) / 100.0
        distancia_min = st.slider("Separación mínima entre picos (muestras)", min_value=1, max_value=50, value=5, step=1)
        n_armonicos = st.slider("Cantidad de armónicos a buscar (1X, 2X...)", min_value=1, max_value=6, value=3)

# Carga de archivo
col_file, col_btn = st.columns([3, 1])
with col_file:
    uploaded_file = st.file_uploader(
        "📁 Arrastra o selecciona el archivo CSV entregado por el equipo:",
        type=["csv", "txt"]
    )
with col_btn:
    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    usar_demo = st.button("🧪 Cargar Medición de Ejemplo", help="Prueba la app con una señal simulada de 1750 RPM.")

df = None
nombre_fuente = ""

if uploaded_file is not None:
    try:
        # Detección flexible de separador (coma o punto y coma)
        df = pd.read_csv(uploaded_file, sep=None, engine='python', decimal='.')
        if df.shape[1] == 1 and ';' in str(df.iloc[0, 0]):
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=';', decimal=',')
        nombre_fuente = uploaded_file.name
    except Exception as e:
        st.error(f"Error al leer el archivo CSV: {e}")
elif usar_demo:
    # Generar señal sintética de prueba: motor a 1750 RPM (29.167 Hz) con armónicos y ruido
    L_demo = 20000
    t_demo = np.arange(L_demo) / fs
    f_real = 1748.5 / 60.0  # 29.14 Hz
    # Señal: 1X + 2X + ruido blanco
    a_demo = (
        0.45 * np.sin(2 * np.pi * f_real * t_demo) +
        0.18 * np.sin(2 * np.pi * (2 * f_real) * t_demo) +
        0.08 * np.sin(2 * np.pi * (3 * f_real) * t_demo) +
        0.05 * np.random.normal(0, 1, L_demo)
    )
    df = pd.DataFrame({"Aceleracion_Z": a_demo})
    nombre_fuente = "Demostración_Motor_1750RPM.csv"

if df is not None:
    st.success(f"✅ Archivo cargado correctamente: **{nombre_fuente}** ({len(df):,} muestras registradas)")
    
    # Selección de columna de aceleración
    col_sel_col, col_info = st.columns([2, 2])
    with col_sel_col:
        opciones_cols = list(df.columns)
        col_seleccionada = st.selectbox(
            "Selecciona la columna con los datos de vibración:",
            options=opciones_cols,
            index=0
        )
    
    try:
        a1 = pd.to_numeric(df[col_seleccionada], errors='coerce').dropna().to_numpy(dtype=float)
        L1 = len(a1)
        
        if L1 < 10:
            st.error("No hay suficientes muestras numéricas en la columna seleccionada.")
            st.stop()
            
        # ========================================================
        # CÁLCULOS MATEMÁTICOS (FFT Y RMS)
        # ========================================================
        RMSa1 = float(np.std(a1, ddof=1))
        
        NFFT1 = 2 ** int(np.ceil(np.log2(L1)))
        f1 = fs / 2 * np.linspace(0, 1, NFFT1 // 2 + 1)
        frecDoma1 = np.fft.fft(a1, NFFT1) / L1
        espectro1 = 2 * np.abs(frecDoma1[:NFFT1 // 2 + 1])
        
        mask = f1 <= freqplot
        f1_plot = f1[mask]
        espectro1_plot = espectro1[mask]
        
        # Detección de picos
        altura_minima = float(espectro1_plot.max() * altura_min_pct)
        picos_idx, _ = find_peaks(espectro1_plot, height=altura_minima, distance=distancia_min)
        picos_freq = f1_plot[picos_idx]
        picos_amp = espectro1_plot[picos_idx]
        
        tabla_picos = pd.DataFrame({'Frecuencia [Hz]': picos_freq, 'Amplitud': picos_amp})
        tabla_picos = tabla_picos.sort_values('Amplitud', ascending=False).reset_index(drop=True)
        
        # Búsqueda del pico correspondiente a 1X
        picos_1x = tabla_picos[np.abs(tabla_picos['Frecuencia [Hz]'] - f_rot) <= tolerancia_hz]
        
        rpm_medida = None
        f_1x_medida = None
        amp_1x_medida = None
        error_rpm_pct = None
        
        if not picos_1x.empty:
            mejor_pico = picos_1x.iloc[0]
            f_1x_medida = mejor_pico['Frecuencia [Hz]']
            amp_1x_medida = mejor_pico['Amplitud']
            rpm_medida = f_1x_medida * 60.0
            error_rpm_pct = ((rpm_medida - rpm_nominal) / rpm_nominal) * 100.0
        
        # ========================================================
        # TARJETAS DE RESULTADOS (KPIS)
        # ========================================================
        st.markdown("### 📊 Resumen de Resultados")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            if rpm_medida is not None:
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #28a745;">
                    <div class="metric-title">🎯 RPM Medida (Real)</div>
                    <div class="metric-value" style="color: #28a745;">{rpm_medida:.1f}</div>
                    <div class="metric-sub">Frecuencia: {f_1x_medida:.2f} Hz</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #dc3545;">
                    <div class="metric-title">🎯 RPM Medida</div>
                    <div class="metric-value" style="color: #dc3545;">No detectada</div>
                    <div class="metric-sub">Fuera de tolerancia (±{tolerancia_hz} Hz)</div>
                </div>
                """, unsafe_allow_html=True)
                
        with c2:
            delta_str = f"{error_rpm_pct:+.2f}%" if error_rpm_pct is not None else "--"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #007bff;">
                <div class="metric-title">📋 RPM Nominal</div>
                <div class="metric-value" style="color: #007bff;">{rpm_nominal:.0f}</div>
                <div class="metric-sub">Desviación: {delta_str}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #17a2b8;">
                <div class="metric-title">📈 Amplitud 1X</div>
                <div class="metric-value" style="color: #17a2b8;">{amp_1x_medida:.4f if amp_1x_medida is not None else 0.0:.4f}</div>
                <div class="metric-sub">Pico fundamental</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c4:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #ffc107;">
                <div class="metric-title">⚡ Vibración Global RMS</div>
                <div class="metric-value" style="color: #856404;">{RMSa1:.4f}</div>
                <div class="metric-sub">m/s²</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        
        # Banner de diagnóstico para los técnicos
        if rpm_medida is not None:
            st.markdown(f"""
            <div class="status-ok">
                ✅ <strong>Lectura Exitosa:</strong> Se detectó la velocidad de giro en <strong>{rpm_medida:.1f} RPM</strong> 
                (Frecuencia fundamental 1X en <strong>{f_1x_medida:.2f} Hz</strong>). 
                La velocidad se encuentra a una diferencia de solo <strong>{abs(rpm_medida - rpm_nominal):.1f} RPM</strong> respecto a la nominal.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-alert">
                ⚠️ <strong>Atención:</strong> No se encontró un pico de vibración predominante exactamente en {f_rot:.2f} Hz (±{tolerancia_hz} Hz).
                Verifica si la RPM nominal ingresada ({rpm_nominal:.0f}) es la correcta o amplía el margen de tolerancia en la barra lateral.
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        
        # ========================================================
        # GRÁFICA INTERACTIVA PLOTLY
        # ========================================================
        st.subheader("📈 Espectro de Frecuencia (FFT)")
        
        fig = go.Figure()
        
        # Traza del espectro
        fig.add_trace(go.Scatter(
            x=f1_plot, y=espectro1_plot, mode='lines', name='Espectro FFT',
            line=dict(color='#1f77b4', width=1.5),
            hovertemplate='Frecuencia: %{x:.2f} Hz<br>Amplitud: %{y:.4f}<extra></extra>'
        ))
        
        # Picos detectados
        fig.add_trace(go.Scatter(
            x=picos_freq, y=picos_amp, mode='markers+text', name='Picos Detectados',
            marker=dict(color='red', size=7, symbol='x'),
            text=[f'{f:.1f} Hz' for f in picos_freq],
            textposition='top center',
            textfont=dict(size=9),
            hovertemplate='Pico<br>Frecuencia: %{x:.2f} Hz<br>Amplitud: %{y:.4f}<extra></extra>'
        ))
        
        # Líneas verticales para los armónicos (1X, 2X, 3X...)
        colores_armonicos = ['#28a745', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        for n in range(1, n_armonicos + 1):
            freq_arm = f_rot * n
            if freq_arm <= freqplot:
                color_linea = colores_armonicos[(n-1) % len(colores_armonicos)]
                fig.add_vline(
                    x=freq_arm, line_dash="dash", line_color=color_linea,
                    annotation_text=f'{n}X ({freq_arm:.1f} Hz)',
                    annotation_position="top left",
                    annotation_font=dict(color=color_linea, size=11, family="sans-serif")
                )
        
        fig.update_layout(
            xaxis_title='Frecuencia [Hz]',
            yaxis_title='Amplitud de Aceleración [m/s²]',
            xaxis_range=[0, freqplot],
            hovermode='closest',
            template='plotly_white',
            margin=dict(l=40, r=20, t=30, b=40),
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ========================================================
        # PESTAÑAS CON DETALLES TÉCNICOS
        # ========================================================
        tab1, tab2, tab3 = st.tabs(["🔍 Análisis de Armónicos (1X, 2X, 3X)", "📋 Tabla de Picos", "⏱️ Señal en el Tiempo"])
        
        with tab1:
            st.markdown("Comparación entre los armónicos esperados de rotación y los picos medidos:")
            filas_armonicos = []
            for n in range(1, n_armonicos + 1):
                freq_esperada = f_rot * n
                cercanos = tabla_picos[np.abs(tabla_picos['Frecuencia [Hz]'] - freq_esperada) <= tolerancia_hz]
                if not cercanos.empty:
                    pico_hallado = cercanos.iloc[0]
                    filas_armonicos.append({
                        "Armónico": f"{n}X",
                        "Frec. Esperada [Hz]": f"{freq_esperada:.2f}",
                        "Frec. Medida [Hz]": f"{pico_hallado['Frecuencia [Hz]']:.2f}",
                        "Amplitud": f"{pico_hallado['Amplitud']:.4f}",
                        "Estado": "✅ Detectado",
                        "RPM Equivalente": f"{pico_hallado['Frecuencia [Hz]'] * 60 / n:.1f}"
                    })
                else:
                    filas_armonicos.append({
                        "Armónico": f"{n}X",
                        "Frec. Esperada [Hz]": f"{freq_esperada:.2f}",
                        "Frec. Medida [Hz]": "--",
                        "Amplitud": "--",
                        "Estado": "⚪ No presente",
                        "RPM Equivalente": "--"
                    })
            st.dataframe(pd.DataFrame(filas_armonicos), use_container_width=True)
            
        with tab2:
            st.markdown("Todos los picos detectados en el rango analizado ordenados por amplitud:")
            st.dataframe(
                tabla_picos.style.format({"Frecuencia [Hz]": "{:.2f}", "Amplitud": "{:.4f}"}),
                use_container_width=True
            )
            
        with tab3:
            # Gráfico de muestra en el tiempo (primeras 500 muestras para no sobrecargar)
            muestras_tiempo = min(500, L1)
            t_sub = np.arange(muestras_tiempo) / fs
            a_sub = a1[:muestras_tiempo]
            
            fig_tiempo = go.Figure()
            fig_tiempo.add_trace(go.Scatter(
                x=t_sub, y=a_sub, mode='lines', name='Vibración',
                line=dict(color='#2ca02c', width=1)
            ))
            fig_tiempo.update_layout(
                title=f'Señal en el Tiempo (Primeras {muestras_tiempo} muestras)',
                xaxis_title='Tiempo [s]',
                yaxis_title='Aceleración [m/s²]',
                template='plotly_white',
                height=350,
                margin=dict(l=40, r=20, t=40, b=40)
            )
            st.plotly_chart(fig_tiempo, use_container_width=True)
            
    except Exception as e:
        st.error(f"Ocurrió un error al procesar los datos: {e}")
        st.exception(e)
else:
    # Estado inicial cuando no hay archivo
    st.info("👆 Por favor sube un archivo CSV arriba o haz clic en **'Cargar Medición de Ejemplo'** para comenzar.")
