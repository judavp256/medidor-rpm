import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks
import datetime

try:
    from report_generator import (generar_imagen_fft, generar_imagen_superposicion,
                                   generar_pdf_reportlab, generar_codigo_latex)
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# ── Configuración de página ─────────────────────────────────────
st.set_page_config(
    page_title="Analizador de RPM | Informe Técnico",
    page_icon="⚙️",
    layout="wide"
)

# ── Paleta institucional (Formato_IT / tema Word) ───────────────
st.markdown("""
<style>
  /* ── Reset y fuente ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── Barra lateral elegante ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f2444 0%, #1F497D 100%) !important;
  }
  [data-testid="stSidebar"] * { color: #e8edf3 !important; }
  [data-testid="stSidebar"] .stSlider > div > div { background: #4F81BD !important; }
  [data-testid="stSidebar"] input { background: rgba(255,255,255,0.1) !important; border-color: rgba(255,255,255,0.25) !important; color: #fff !important; }
  [data-testid="stSidebar"] label { color: #b8cfe4 !important; font-size: 0.8rem !important; font-weight: 500 !important; }
  [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
  [data-testid="stSidebar"] .stSelectbox > div { background: rgba(255,255,255,0.08) !important; }

  /* ── Fondo principal ── */
  [data-testid="stAppViewContainer"] { background-color: #f0f4f8; }
  [data-testid="stMain"] { background-color: #f0f4f8; }

  /* ── Tarjetas KPI ── */
  .kpi-card {
    background: white;
    border-radius: 12px;
    padding: 18px 14px;
    border-top: 4px solid #4F81BD;
    box-shadow: 0 2px 12px rgba(31,73,125,0.08);
    text-align: center;
    transition: box-shadow 0.2s;
  }
  .kpi-card:hover { box-shadow: 0 4px 20px rgba(31,73,125,0.15); }
  .kpi-card.accent-green { border-top-color: #1a7f4e; }
  .kpi-card.accent-red   { border-top-color: #c0392b; }
  .kpi-card.accent-amber { border-top-color: #d4870d; }
  .kpi-card.accent-purple{ border-top-color: #6f42c1; }

  .kpi-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6b7a8d;
    margin-bottom: 4px;
  }
  .kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0f2444;
    line-height: 1.1;
  }
  .kpi-value.green  { color: #1a7f4e; }
  .kpi-value.red    { color: #c0392b; }
  .kpi-value.blue   { color: #1F497D; }
  .kpi-value.amber  { color: #d4870d; }
  .kpi-value.purple { color: #6f42c1; }
  .kpi-sub {
    font-size: 0.75rem;
    color: #8a96a3;
    margin-top: 3px;
  }

  /* ── Sección card ── */
  .section-card {
    background: white;
    border-radius: 12px;
    padding: 20px 22px;
    box-shadow: 0 1px 8px rgba(31,73,125,0.07);
    margin-bottom: 18px;
  }
  .section-title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #1F497D;
    border-left: 4px solid #4F81BD;
    padding-left: 10px;
    margin-bottom: 14px;
  }

  /* ── Banners de estado ── */
  .banner-ok {
    background: linear-gradient(135deg, #e8f5ee 0%, #d4edda 100%);
    border-left: 5px solid #1a7f4e;
    border-radius: 8px;
    padding: 14px 16px;
    color: #155724;
    font-size: 0.88rem;
  }
  .banner-warn {
    background: linear-gradient(135deg, #fffbea 0%, #fff3cd 100%);
    border-left: 5px solid #d4870d;
    border-radius: 8px;
    padding: 14px 16px;
    color: #7a4f0a;
    font-size: 0.88rem;
  }
  .banner-info {
    background: linear-gradient(135deg, #e8f0fc 0%, #dce8fb 100%);
    border-left: 5px solid #4F81BD;
    border-radius: 8px;
    padding: 14px 16px;
    color: #1F497D;
    font-size: 0.88rem;
  }

  /* ── Slots de carga ── */
  .slot-neutral { border-left-color: #4F81BD !important; }
  .slot-diff    { border-left-color: #c0392b !important; }

  /* ── Header personalizado ── */
  .app-header {
    background: linear-gradient(100deg, #0f2444 0%, #1F497D 60%, #2563a8 100%);
    border-radius: 14px;
    padding: 22px 28px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 20px rgba(15,36,68,0.3);
  }
  .app-header h1 {
    color: white !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    letter-spacing: -0.01em;
  }
  .app-header p { color: #b8cfe4; font-size: 0.8rem; margin: 4px 0 0 0; }
  .badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    color: #c8f7c5;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.04em;
  }

  /* ── Form inputs ── */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stNumberInput > div > div > input {
    border-radius: 8px !important;
    border-color: #d0dce8 !important;
    font-size: 0.88rem !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus {
    border-color: #4F81BD !important;
    box-shadow: 0 0 0 3px rgba(79,129,189,0.15) !important;
  }

  /* ── Botones ── */
  .stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
  }
  .stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    background: #1F497D !important;
    color: white !important;
    border: none !important;
  }
  .stDownloadButton > button:hover { background: #2563a8 !important; }

  /* ── Divider ── */
  hr { border-color: #dce8f0 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# 1. AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════════
PASSWORD = "tecnico2026"
try:
    PASSWORD = st.secrets.get("PASSWORD", PASSWORD)
except Exception:
    pass

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    col_l, col_m, col_r = st.columns([1, 1.1, 1])
    with col_m:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center; margin-bottom:28px;'>
          <div style='font-size:3rem;'>⚙️</div>
          <h2 style='color:#0f2444; margin:8px 0 4px;'>Analizador de RPM</h2>
          <p style='color:#6b7a8d; font-size:0.88rem;'>Plataforma técnica de análisis espectral de vibraciones</p>
        </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("Contraseña de acceso:", type="password", label_visibility="collapsed",
                            placeholder="Ingresa la contraseña...")
        if st.button("🔑 Ingresar a la Plataforma", use_container_width=True):
            if pwd == PASSWORD:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
        st.caption(f"🔐 Contraseña: `{PASSWORD}`  ·  Procesamiento 100% volátil — cero almacenamiento en nube")
    st.stop()


# ══════════════════════════════════════════════════════════════════
# 2. HEADER GERENCIAL
# ══════════════════════════════════════════════════════════════════
col_hd, col_logout = st.columns([4, 1])
with col_hd:
    st.markdown("""
    <div class="app-header">
      <div>
        <h1>⚙️ Analizador de RPM por Vibración</h1>
        <p>Determinación de velocidad de giro · Análisis espectral FFT · Informe Técnico Oficial</p>
      </div>
      <div>
        <span class="badge">🔒 CERO ALMACENAMIENTO EN NUBE</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["auth"] = False
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# 3. BARRA LATERAL — Parámetros
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔧 Parámetros del Equipo")
    rpm_nominal = st.number_input("RPM Nominal de Placa", 1.0, 100000.0, 1750.0, 50.0)
    f_rot = rpm_nominal / 60.0
    st.caption(f"Frecuencia 1X: **{f_rot:.2f} Hz**")

    st.markdown("---")
    st.markdown("## 🎛️ Configuración del Sensor")
    freqplot = st.number_input(
        "Frecuencia máx. visualización [Hz]",
        min_value=10, max_value=5000, value=200, step=20,
        help="Predeterminado en 200 Hz (valor original del código)."
    )
    fs = st.number_input("Frecuencia de Muestreo (Fs) [Hz]", 100, 200000, 11628, 100)

    st.markdown("---")
    with st.expander("🛠️ Ajustes de Detección"):
        tolerancia_hz  = st.number_input("Tolerancia armónicos (± Hz)", 0.1, 10.0, 1.5, 0.1)
        altura_min_pct = st.slider("Sensibilidad picos (% máx)", 1, 50, 10) / 100.0
        distancia_min  = st.slider("Separación mínima entre picos", 1, 50, 5)
        n_armonicos    = st.slider("Armónicos a marcar (1X, 2X…)", 1, 5, 3)


# ══════════════════════════════════════════════════════════════════
# 4. FUNCIONES DE ANÁLISIS
# ══════════════════════════════════════════════════════════════════
def calcular_fft(arr, sr, fmax):
    L = len(arr)
    rms = float(np.std(arr, ddof=1))
    nfft = 2 ** int(np.ceil(np.log2(L)))
    f = sr / 2 * np.linspace(0, 1, nfft // 2 + 1)
    spec = 2 * np.abs(np.fft.fft(arr, nfft)[:nfft // 2 + 1]) / L
    m = f <= fmax
    return f[m], spec[m], rms


def analizar_picos(f_plot, esp, f_obj, tol, min_pct, dist_min):
    alt = float(esp.max() * min_pct)
    idx, _ = find_peaks(esp, height=alt, distance=dist_min)
    pf, pa = f_plot[idx], esp[idx]
    df_p = pd.DataFrame({'Frecuencia [Hz]': pf, 'Amplitud': pa})
    df_p = df_p.sort_values('Amplitud', ascending=False).reset_index(drop=True)
    near = df_p[np.abs(df_p['Frecuencia [Hz]'] - f_obj) <= tol]
    if not near.empty:
        b = near.iloc[0]
        return b['Frecuencia [Hz]'], b['Amplitud'], pf, pa
    return None, None, pf, pa


def parsear_csv(archivo):
    try:
        df = pd.read_csv(archivo, sep=None, engine='python', decimal='.')
        col = df.columns[0]
        arr = pd.to_numeric(df[col], errors='coerce').dropna().to_numpy(dtype=float)
        return arr if len(arr) >= 10 else None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════
# 5. SLOTS DE CARGA (FLEXIBLE, NO RESTRICTIVO)
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-card">
  <div class="section-title">📁 Carga de Archivos de Medición</div>
</div>
""", unsafe_allow_html=True)

with st.container():
    col_desc, col_demo = st.columns([3, 1])
    with col_desc:
        st.caption("Carga de 1 a 4 mediciones. Ningún slot es obligatorio — la plataforma se adapta a los archivos disponibles.")
    with col_demo:
        usar_demo = st.button("🧪 Demo (4 mediciones simuladas)", use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f1 = st.file_uploader("Medición 1", type=["csv","txt"], key="f1",
                               label_visibility="visible")
    with c2:
        f2 = st.file_uploader("Medición 2 *(Opcional)*", type=["csv","txt"], key="f2",
                               label_visibility="visible")
    with c3:
        f3 = st.file_uploader("Medición 3 *(Opcional)*", type=["csv","txt"], key="f3",
                               label_visibility="visible")
    with c4:
        f4 = st.file_uploader("Medición 4 — Condición Diferente *(Opcional)*",
                               type=["csv","txt"], key="f4", label_visibility="visible")

archivos_cargados = []

if usar_demo:
    L = int(fs * 1.5); t = np.arange(L) / fs
    for i, fr in enumerate([29.14, 29.16, 29.13]):
        s = (0.45*np.sin(2*np.pi*fr*t) + 0.18*np.sin(2*np.pi*2*fr*t) +
             0.08*np.sin(2*np.pi*3*fr*t) + np.random.normal(0, 0.04, L))
        archivos_cargados.append({'slot': i+1, 'nombre': f'Demo_Medicion_{i+1}.csv',
                                   'tipo': 'base', 'data': s})
    fc = 27.0
    sc = (0.38*np.sin(2*np.pi*fc*t) + 0.22*np.sin(2*np.pi*2*fc*t) +
          np.random.normal(0, 0.05, L))
    archivos_cargados.append({'slot': 4, 'nombre': 'Demo_Medicion_4_diferente.csv',
                               'tipo': 'diferente', 'data': sc})
    st.info("💡 Modo Demo activado: mediciones 1–3 a ~1748 RPM · Medición 4 a ~1620 RPM")
else:
    for i, fobj in enumerate([f1, f2, f3, f4]):
        if fobj:
            arr = parsear_csv(fobj)
            if arr is not None:
                # La 4ta es "diferente condición" solo si ya hay 3 base
                base_count = sum(1 for a in archivos_cargados if a['tipo'] == 'base')
                tipo = 'diferente' if (i == 3 and base_count >= 1) else 'base'
                archivos_cargados.append({'slot': i+1, 'nombre': fobj.name,
                                           'tipo': tipo, 'data': arr})


# ══════════════════════════════════════════════════════════════════
# 6. PROCESAMIENTO Y RESULTADOS
# ══════════════════════════════════════════════════════════════════
COLORES_BASE = ['#1F497D', '#2980b9', '#1a7f4e', '#6f42c1']
COLOR_DIFF   = '#c0392b'

if archivos_cargados:
    ensayos_base = []
    ensayo_dif   = None
    imagenes_pdf = []

    for item in archivos_cargados:
        f_plot, esp, rms = calcular_fft(item['data'], fs, freqplot)
        f_1x, amp_1x, pf, pa = analizar_picos(f_plot, esp, f_rot,
                                               tolerancia_hz, altura_min_pct, distancia_min)
        rpm = f_1x * 60.0 if f_1x else None

        obj = {**item, 'f_plot': f_plot, 'espectro_plot': esp, 'rms': rms,
               'f_1x': f_1x, 'amp_1x': amp_1x, 'rpm': rpm,
               'p_freq': pf, 'p_amp': pa,
               'color': (COLOR_DIFF if item['tipo'] == 'diferente'
                         else COLORES_BASE[len(ensayos_base) % len(COLORES_BASE)])}

        if item['tipo'] == 'base':
            ensayos_base.append(obj)
        else:
            ensayo_dif = obj

        if REPORTLAB_OK:
            lbl = f"Medición {item['slot']} ({'Diferente' if item['tipo']=='diferente' else 'Base'})"
            img_buf = generar_imagen_fft(f_plot, esp, f_1x, amp_1x, f_rot,
                                         n_armonicos, lbl, obj['color'])
            imagenes_pdf.append((lbl, img_buf))

    # Superposición
    if REPORTLAB_OK and len(archivos_cargados) >= 2:
        sup_buf = generar_imagen_superposicion(
            [*ensayos_base, *([ensayo_dif] if ensayo_dif else [])], f_rot, n_armonicos)
        imagenes_pdf.append(('Superposición de Todos los Espectros', sup_buf))

    # ── Estadísticas globales ──
    rpms_v   = [r['rpm'] for r in ensayos_base if r['rpm']]
    rpm_prom = np.mean(rpms_v) if rpms_v else None
    rpm_std  = float(np.std(rpms_v, ddof=1)) if len(rpms_v) > 1 else 0.0
    f1x_prom = rpm_prom / 60.0 if rpm_prom else None
    rms_prom = float(np.mean([r['rms'] for r in ensayos_base])) if ensayos_base else 0.0

    # ── TARJETAS KPI GERENCIALES ──────────────────────────────────
    st.markdown("### Indicadores Clave")
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        if rpm_prom:
            st.markdown(f"""
            <div class="kpi-card accent-green">
              <div class="kpi-label">🎯 RPM Promedio Real</div>
              <div class="kpi-value green">{rpm_prom:.1f}</div>
              <div class="kpi-sub">Frec. fundamental: {f1x_prom:.2f} Hz</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi-card accent-red">
              <div class="kpi-label">🎯 RPM Promedio</div>
              <div class="kpi-value red">— —</div>
              <div class="kpi-sub">Sin pico detectado en rango</div>
            </div>""", unsafe_allow_html=True)

    with k2:
        delta = f"{((rpm_prom-rpm_nominal)/rpm_nominal*100):+.2f}%" if rpm_prom else "—"
        disp  = f"± {rpm_std:.2f} RPM" if len(rpms_v) > 1 else ("1 medición" if rpms_v else "—")
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">📋 Repetibilidad</div>
          <div class="kpi-value blue">{disp}</div>
          <div class="kpi-sub">Desviación respecto a placa: {delta}</div>
        </div>""", unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card accent-amber">
          <div class="kpi-label">⚡ Vibración Global RMS</div>
          <div class="kpi-value amber">{rms_prom:.4f}</div>
          <div class="kpi-sub">m/s² — promedio de mediciones base</div>
        </div>""", unsafe_allow_html=True)

    with k4:
        n_tot = len(archivos_cargados)
        n_ok  = len([r for r in ensayos_base if r['rpm']])
        col_coh = "green" if n_ok == len(ensayos_base) and ensayos_base else "amber"
        st.markdown(f"""
        <div class="kpi-card accent-purple">
          <div class="kpi-label">🔍 Coherencia</div>
          <div class="kpi-value purple">{n_ok}/{len(ensayos_base)}</div>
          <div class="kpi-sub">{n_tot} archivo(s) cargado(s) · {1 if ensayo_dif else 0} cond. diferente</div>
        </div>""", unsafe_allow_html=True)

    st.write("")

    # ── Banner de diagnóstico ──────────────────────────────────────
    if ensayo_dif and ensayo_dif.get('rpm') and rpm_prom:
        delta_rpm = rpm_prom - ensayo_dif['rpm']
        pct = abs(delta_rpm / rpm_prom) * 100.0
        if delta_rpm > 0:
            st.markdown(f"""
            <div class="banner-ok">
              🎯 <strong>DIAGNÓSTICO — DIFERENCIA CONFIRMADA:</strong><br>
              Las mediciones base registraron <strong>{rpm_prom:.1f} RPM</strong>.
              La Medición 4 (condición diferente) registró <strong>{ensayo_dif['rpm']:.1f} RPM</strong>,
              una reducción de <strong>{delta_rpm:.1f} RPM ({pct:.1f}%)</strong>.<br>
              ✅ Esto confirma que el pico identificado corresponde a la rotación mecánica real del eje.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="banner-warn">
              ⚠️ <strong>Medición 4:</strong> Registró <strong>{ensayo_dif['rpm']:.1f} RPM</strong>
              ({abs(delta_rpm):.1f} RPM de diferencia respecto a la base).
            </div>""", unsafe_allow_html=True)
    elif rpm_prom:
        st.markdown(f"""
        <div class="banner-info">
          ✅ <strong>Mediciones base procesadas:</strong> {rpm_prom:.1f} RPM promedio.
          Carga una Medición 4 con condición diferente para validar el pico.
        </div>""", unsafe_allow_html=True)

    st.write("")

    # ══════════════════════════════════════════════════════════════
    # 7. 5 GRÁFICOS APILADOS VERTICALMENTE (4 individuales + 1 superposición)
    # ══════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="section-title">📈 Espectros de Frecuencia (FFT) — Individuales y Comparativo</div>
    """, unsafe_allow_html=True)
    st.caption(f"Rango mostrado: **0 – {freqplot} Hz** · Frecuencia de referencia 1X: **{f_rot:.2f} Hz** "
               f"({rpm_nominal:.0f} RPM nominal)")

    todos_ensayos = [*ensayos_base, *([ensayo_dif] if ensayo_dif else [])]

    for e in todos_ensayos:
        es_dif   = e['tipo'] == 'diferente'
        etiqueta = f"Medición {e['slot']} — {'Condición Diferente' if es_dif else 'Condición Base'}"
        rpm_lbl  = f"{e['rpm']:.1f} RPM" if e['rpm'] else "Sin pico detectado"

        fig = go.Figure()

        # Espectro
        fig.add_trace(go.Scatter(
            x=e['f_plot'], y=e['espectro_plot'], mode='lines',
            name='Espectro FFT',
            line=dict(color=e['color'], width=1.8),
            hovertemplate='<b>%{x:.2f} Hz</b><br>Amplitud: %{y:.5f} m/s²<extra></extra>'
        ))

        # Pico fundamental
        if e['f_1x']:
            fig.add_trace(go.Scatter(
                x=[e['f_1x']], y=[e['amp_1x']], mode='markers+text',
                marker=dict(color='#c0392b', size=10, symbol='x', line=dict(width=2)),
                text=[f"<b>{e['f_1x']:.2f} Hz<br>{e['rpm']:.0f} RPM</b>"],
                textposition='top center',
                textfont=dict(size=10, color='#c0392b'),
                name='1X detectado', showlegend=True
            ))

        # Líneas armónicas
        for n in range(1, n_armonicos + 1):
            fa = f_rot * n
            if fa <= freqplot:
                fig.add_vline(x=fa, line_dash='dot', line_color='#888',
                              line_width=1,
                              annotation_text=f'{n}X·{fa:.1f}Hz',
                              annotation_position='top left',
                              annotation_font=dict(size=9, color='#777'))

        fig.update_layout(
            title=dict(text=f"<b>{etiqueta}</b>  ·  {rpm_lbl}  ·  RMS {e['rms']:.4f} m/s²",
                       font=dict(size=13, color='#0f2444'), x=0),
            xaxis=dict(title='Frecuencia [Hz]', range=[0, freqplot],
                       gridcolor='#e8edf3', linecolor='#c5d0dc'),
            yaxis=dict(title='Amplitud [m/s²]',
                       gridcolor='#e8edf3', linecolor='#c5d0dc'),
            paper_bgcolor='white', plot_bgcolor='white',
            margin=dict(l=50, r=20, t=50, b=45),
            height=340,
            hovermode='x unified',
            legend=dict(orientation='h', x=1, xanchor='right', y=1.12),
            shapes=[dict(type='rect', xref='paper', yref='paper',
                         x0=0, y0=0, x1=1, y1=1,
                         line=dict(color='#dce8f0', width=1))]
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Gráfico 5: Superposición ───────────────────────────────────
    if len(todos_ensayos) >= 2:
        st.markdown("---")
        fig_sup = go.Figure()

        for e in todos_ensayos:
            rpm_lb = f"{e['rpm']:.1f} RPM" if e['rpm'] else "sin pico"
            lbl = f"Medición {e['slot']} ({'Dif.' if e['tipo']=='diferente' else 'Base'}) · {rpm_lb}"
            fig_sup.add_trace(go.Scatter(
                x=e['f_plot'], y=e['espectro_plot'], mode='lines', name=lbl,
                line=dict(color=e['color'], width=1.6,
                           dash='dash' if e['tipo']=='diferente' else 'solid'),
                hovertemplate=f"<b>Medición {e['slot']}</b><br>%{{x:.2f}} Hz · %{{y:.5f}}<extra></extra>"
            ))

        for n in range(1, n_armonicos + 1):
            fa = f_rot * n
            if fa <= freqplot:
                fig_sup.add_vline(x=fa, line_dash='dot', line_color='#aaa', line_width=1,
                                  annotation_text=f'{n}X', annotation_font=dict(size=9, color='#888'))

        fig_sup.update_layout(
            title=dict(text='<b>Gráfico Comparativo — Superposición de Todos los Espectros</b>',
                       font=dict(size=13, color='#0f2444'), x=0),
            xaxis=dict(title='Frecuencia [Hz]', range=[0, freqplot],
                       gridcolor='#e8edf3', linecolor='#c5d0dc'),
            yaxis=dict(title='Amplitud [m/s²]',
                       gridcolor='#e8edf3', linecolor='#c5d0dc'),
            paper_bgcolor='white', plot_bgcolor='white',
            margin=dict(l=50, r=20, t=50, b=45),
            height=400,
            hovermode='x unified',
            legend=dict(orientation='h', y=-0.22, x=0)
        )
        st.plotly_chart(fig_sup, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # 8. FORMULARIO DE INFORME TÉCNICO
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("""
    <div class="section-title">📄 Generación del Informe Técnico Oficial (Formato IT)</div>
    """, unsafe_allow_html=True)
    st.caption("Completa los campos para generar el informe institucional fiel al Formato_IT_NUEVO.docx")

    with st.form("informe_form"):
        tab_meta, tab_cont, tab_resp = st.tabs(["📋 Metadatos", "📝 Contenido Técnico", "✍️ Responsables"])

        with tab_meta:
            ci1, ci2 = st.columns(2)
            with ci1:
                i_proyecto    = st.text_input("Proyecto / Iniciativa", "Evaluación de RPM por Vibraciones")
                i_modulo      = st.text_input("Módulo", "Producto portafolio")
                i_categoria   = st.text_input("Categoría de Producto", "Refrigeración")
                i_tipo        = st.text_input("Tipo de Proyecto", "Portafolio")
            with ci2:
                i_referencia  = st.text_input("Referencia del Equipo", "N/A")
                i_costo       = st.text_input("Centro de Costo", "")
                i_estado      = st.selectbox("Estado", ["En curso","Completado","Aprobado"])
                i_avance      = st.text_input("Avance (%)", "100%")
            i_fecha = st.date_input("Fecha del Ensayo", datetime.date.today()).strftime("%d/%m/%Y")
            i_palabras = st.text_input("Palabras Clave", "Vibración, RPM, FFT, Acelerómetro")

        with tab_cont:
            i_objetivo    = st.text_area("Objetivo del Ensayo",
                "Determinar con exactitud la velocidad angular de régimen (RPM) "
                "mediante análisis FFT de señales de vibración.", height=60)
            i_aspectos    = st.text_area("Aspectos Preliminares",
                "Se realizó la caracterización dinámica del equipo bajo análisis "
                "conectando un acelerómetro uniaxial al artefacto en condición operativa.", height=70)
            ci3, ci4 = st.columns(2)
            with ci3:
                i_conclusiones = st.text_area("Conclusiones",
                    f"La velocidad de rotación en condición base se determinó en "
                    f"{rpm_prom:.1f} RPM." if rpm_prom else "Medición ejecutada satisfactoriamente.",
                    height=90)
            with ci4:
                i_observaciones = st.text_area("Observaciones",
                    "Se recomienda continuar el monitoreo periódico de los niveles de vibración.",
                    height=90)

        with tab_resp:
            cr1, cr2, cr3 = st.columns(3)
            with cr1:
                i_realizo = st.text_input("Realizó (Técnico)", "Técnico de Ensayos")
            with cr2:
                i_reviso  = st.text_input("Revisó (Ingeniero)", "Ing. Vibraciones")
            with cr3:
                i_aprobo  = st.text_input("Aprobó (Líder)", "Director de Laboratorio")

        btn_gen = st.form_submit_button("⚡ Generar Informe Técnico", use_container_width=True)

    if btn_gen:
        st.session_state["informe_listo"] = True
        meta = dict(
            proyecto=i_proyecto, modulo=i_modulo, categoria=i_categoria,
            tipo_proyecto=i_tipo, referencia=i_referencia, centro_costo=i_costo,
            estado=i_estado, avance=i_avance, fecha=i_fecha,
            objetivo=i_objetivo, palabras_clave=i_palabras,
            aspectos_preliminares=i_aspectos,
            conclusiones=i_conclusiones, observaciones=i_observaciones,
            responsable_realizo=i_realizo, responsable_reviso=i_reviso,
            responsable_aprobo=i_aprobo
        )
        params = dict(rpm_nominal=rpm_nominal, fs=fs, freqplot=freqplot, tolerancia_hz=tolerancia_hz)
        st.session_state["meta_guardada"]   = meta
        st.session_state["params_guardados"] = params

    if st.session_state.get("informe_listo"):
        meta   = st.session_state["meta_guardada"]
        params = st.session_state["params_guardados"]

        dc1, dc2 = st.columns(2)

        if REPORTLAB_OK:
            try:
                pdf_bytes = generar_pdf_reportlab(
                    meta, params, ensayos_base, rpm_prom, rpm_std, rms_prom,
                    ensayo_dif, imagenes_pdf
                )
                ref = meta.get('referencia','IT')
                fecha_fn = datetime.date.today().strftime('%Y%m%d')
                with dc1:
                    st.download_button(
                        "📥 Descargar Informe Técnico PDF",
                        pdf_bytes,
                        f"InformeTecnico_{ref}_{fecha_fn}.pdf",
                        "application/pdf",
                        use_container_width=True
                    )
            except Exception as ex:
                dc1.error(f"Error PDF: {ex}")
        else:
            dc1.warning("Instala `reportlab` para generar PDF.")

        try:
            tex = generar_codigo_latex(meta, params, ensayos_base, rpm_prom, rpm_std, rms_prom, ensayo_dif)
            with dc2:
                st.download_button(
                    "📥 Descargar Código LaTeX (.tex)",
                    tex, f"InformeTecnico_{meta.get('referencia','IT')}.tex",
                    "text/plain", use_container_width=True
                )
        except Exception as ex:
            dc2.error(f"Error LaTeX: {ex}")

else:
    st.markdown("""
    <div class="banner-info" style="text-align:center; padding: 32px;">
      <div style="font-size:2.5rem; margin-bottom:10px;">📁</div>
      <strong>Sube al menos un archivo CSV en los slots superiores</strong><br>
      o haz clic en <em>"🧪 Demo"</em> para ver la plataforma en acción.
    </div>""", unsafe_allow_html=True)
