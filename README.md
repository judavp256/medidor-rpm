# ⚙️ Medidor de RPM por Vibración (Acelerómetro)

Aplicación web diseñada específicamente para **técnicos y operarios de campo**, que permite determinar las **RPM reales de giro de un equipo** mediante el análisis espectral (FFT) de las vibraciones registradas por un acelerómetro.

---

## 🚀 ¿Cómo ponerlo en línea con GitHub?

Tienes **dos opciones gratuitas** listas para usar. Elige la que prefieras:

### Opción 1: Streamlit Community Cloud (Recomendada para Python)
Esta opción corre la aplicación completa en Python (`app.py`) en los servidores de Streamlit conectados a tu GitHub.

1. **Sube esta carpeta a un nuevo repositorio en tu cuenta de GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Tacómetro digital por vibración"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/medidor-rpm.git
   git push -u origin main
   ```
2. Entra a **[share.streamlit.io](https://share.streamlit.io)** e inicia sesión con tu cuenta de GitHub.
3. Haz clic en **"New app"** y selecciona:
   * **Repository:** `TU-USUARIO/medidor-rpm`
   * **Branch:** `main`
   * **Main file path:** `app.py`
4. Haz clic en **"Deploy"**.
5. ¡Listo! En 1 minuto tendrás un enlace público (ejemplo: `https://medidor-rpm.streamlit.app`) que tus técnicos pueden abrir desde su celular, tablet o computador.

---

### Opción 2: GitHub Pages (100% en el Navegador, sin servidores)
El archivo `index.html` incluido en este proyecto es una versión web completa construida con Tailwind CSS, Plotly.js y cálculo FFT en JavaScript.

1. Sube los archivos a tu repositorio de GitHub (igual que en el paso 1 de arriba).
2. En GitHub, entra a la pestaña **Settings** (Configuración) de tu repositorio.
3. En el menú lateral izquierdo, haz clic en **Pages**.
4. En la sección **"Build and deployment"**:
   * **Source:** `Deploy from a branch`
   * **Branch:** Selecciona `main` y la carpeta `/ (root)`.
   * Haz clic en **Save**.
5. En 1 o 2 minutos, GitHub te dará una URL directa como:
   `https://TU-USUARIO.github.io/medidor-rpm/`

---

## 📋 ¿Cómo la usan los técnicos?

1. **Ingresan la RPM Nominal:** Escriben el valor de la placa del motor (por ejemplo `1750`).
2. **Cargan el CSV:** Arrastran el archivo CSV que descargaron del acelerómetro.
3. **Lectura Inmediata:** La interfaz muestra directamente:
   * 🎯 **RPM Medida (Real):** La velocidad calculada a partir del pico fundamental de vibración (1X).
   * 📋 **RPM Nominal y Desviación:** El porcentaje de diferencia con la placa.
   * ⚡ **Nivel de Vibración RMS:** En $\text{m/s}^2$ para evaluar el estado general de vibración.
   * 📈 **Gráfico del Espectro:** Con líneas guía para los armónicos 1X, 2X y 3X.
   * 🔍 **Diagnóstico de Armónicos:** Permite detectar posibles desbalances o desalineaciones mecánicas si los armónicos 2X o 3X tienen amplitudes elevadas.

---

## 📁 Archivos del Proyecto

* **`app.py`**: Aplicación web completa en Python (Streamlit).
* **`requirements.txt`**: Dependencias para el despliegue automático en la nube.
* **`index.html`**: Versión web estática para GitHub Pages directa.
* **`ejemplo_acelerometro.csv`**: Archivo de prueba sintético (motor simulado a 1748.5 RPM, $F_s = 11628\text{ Hz}$).
