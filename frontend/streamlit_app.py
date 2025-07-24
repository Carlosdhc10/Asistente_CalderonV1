import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

# Configuración de la app
st.set_page_config(page_title="Asistente Sequía Calderón", page_icon="💧", layout="wide")
st.title("💧 Asistente de Análisis de Sequías - Calderón")

DATA_PATH = os.path.join("data", "C20-Calderón_Precipitación-Diario.csv")

@st.cache_data(show_spinner=False)
def cargar_datos():
    try:
        df = pd.read_csv(DATA_PATH, parse_dates=["fecha"])
        return df
    except Exception as e:
        st.error(f"❌ No se pudo cargar el archivo CSV: {e}")
        return pd.DataFrame()

def interpretar_grafica(prompt: str, modelo: str) -> str:
    try:
        with st.spinner("Consultando al asistente IA..."):
            response = requests.post(
                "http://localhost:8000/chatbot",
                json={"pregunta": prompt, "modelo": modelo.lower()},
                timeout=20
            )
        if response.status_code == 200:
            return response.json().get("respuesta", "Sin respuesta.")
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error al conectar con el backend: {e}"

# Inicializar estados de sesión para interpretaciones
if "interpretaciones" not in st.session_state:
    st.session_state.interpretaciones = {
        "registros": "",
        "tendencia": "",
        "dispersion": "",
        "histograma": ""
    }

tab1, tab2, tab3, tab4 = st.tabs(["🤖 Asistente Conversacional", "📡 Análisis de Datos", "⬆️ Subir tus propios datos", "📄 Generar Reporte y Enviar Correo"])

with tab1:
    st.subheader("Haz preguntas sobre la sequía o el suministro de agua ❓")

    if "historial" not in st.session_state:
        st.session_state.historial = []

    if "input_pregunta" not in st.session_state:
        st.session_state.input_pregunta = ""

    if "modelo_seleccionado" not in st.session_state:
        st.session_state.modelo_seleccionado = "OpenAI"

    modelo_opciones = ["OpenAI", "HuggingFace"]
    modelo_elegido = st.selectbox(
        "Selecciona el modelo de lenguaje:", 
        modelo_opciones, 
        index=modelo_opciones.index(st.session_state.modelo_seleccionado)
    )
    st.session_state.modelo_seleccionado = modelo_elegido

    def enviar_pregunta():
        pregunta = st.session_state.input_pregunta.strip()
        if not pregunta:
            st.warning("Por favor, ingresa una pregunta válida.")
            return
        try:
            with st.spinner("Consultando al asistente..."):
                response = requests.post(
                    "http://localhost:8000/chatbot",
                    json={"pregunta": pregunta, "modelo": st.session_state.modelo_seleccionado.lower()},
                    timeout=15
                )
            if response.status_code == 200:
                respuesta = response.json().get("respuesta", "Sin respuesta.")
                st.session_state.historial.append({
                    "pregunta": pregunta,
                    "respuesta": respuesta,
                    "modelo": st.session_state.modelo_seleccionado
                })
                st.session_state.input_pregunta = ""
            else:
                st.error(f"Error al contactar con el backend: {response.status_code}")
        except requests.exceptions.Timeout:
            st.error("El servidor no respondió a tiempo. Intenta de nuevo más tarde.")
        except Exception as e:
            st.error(f"No se pudo conectar con el backend: {e}")

    st.text_input("Tu pregunta:", key="input_pregunta", on_change=enviar_pregunta)

    for turno in st.session_state.historial:
        st.markdown(f"**Modelo ({turno['modelo']}):**")
        st.markdown(f"**Tú:** {turno['pregunta']}")
        st.markdown(f"**Asistente:** {turno['respuesta']}")
        st.markdown("---")

with tab2:
    st.subheader("💧 Explora los datos históricos del suministro de agua")

    df = cargar_datos()
    if df.empty:
        st.stop()

    if not {"fecha", "valor"}.issubset(df.columns):
        st.error("El archivo debe contener las columnas 'fecha' y 'valor'.")
        st.stop()

    df["año"] = df["fecha"].dt.year

    # Función local para solicitar interpretación y actualizar estado
    def solicitar_interpretacion(clave, prompt):
        resp = interpretar_grafica(prompt, st.session_state.modelo_seleccionado)
        st.session_state.interpretaciones[clave] = resp

    # Número de registros por año
    st.markdown("📊 ### Número de registros por año")
    st.bar_chart(df.groupby("año").size())
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Interpretar con IA - Registros por año"):
            prompt = (
                "Analiza el gráfico de barras titulado Número de registros por año. Describe la tendencia "
                "del Número de registros desde 2020 hasta 2025. Específicamente, identifica el año con la menor "
                "cantidad de registros, los años con la mayor cantidad consistente de registros y explica el cambio "
                "aparente observado en el año 2025, teniendo en cuenta que los datos para 2025 podrían ser parciales. "
                "Hipotetiza qué podría causar este patrón en el número de registros a lo largo de estos años."
            )
            solicitar_interpretacion("registros", prompt)
    with col2:
        if st.button("Limpiar interpretación - Registros"):
            st.session_state.interpretaciones["registros"] = ""

    if st.session_state.interpretaciones["registros"]:
        st.info(st.session_state.interpretaciones["registros"])

    # Tendencia temporal
    st.markdown("📊 ### Variación de disponibilidad de agua a lo largo del tiempo")
    st.plotly_chart(px.line(df, x="fecha", y="valor", title="Tendencia de disponibilidad de agua"), use_container_width=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Interpretar con IA - Tendencia temporal"):
            prompt = "Interpreta la tendencia de la disponibilidad de agua en Calderón según la gráfica de línea generada."
            solicitar_interpretacion("tendencia", prompt)
    with col2:
        if st.button("Limpiar interpretación - Tendencia"):
            st.session_state.interpretaciones["tendencia"] = ""

    if st.session_state.interpretaciones["tendencia"]:
        st.info(st.session_state.interpretaciones["tendencia"])

    # Dispersión
    st.markdown("📊 ### Dispersión de valores en el tiempo")
    st.plotly_chart(px.scatter(df, x="fecha", y="valor", title="Dispersión del indicador 'valor'"), use_container_width=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Interpretar con IA - Dispersión temporal"):
            prompt = "Describe la dispersión de los valores de disponibilidad de agua en el tiempo en Calderón."
            solicitar_interpretacion("dispersion", prompt)
    with col2:
        if st.button("Limpiar interpretación - Dispersión"):
            st.session_state.interpretaciones["dispersion"] = ""

    if st.session_state.interpretaciones["dispersion"]:
        st.info(st.session_state.interpretaciones["dispersion"])

    # Histograma
    st.markdown("📊 ### Distribución del indicador 'valor' (Histograma)")
    st.plotly_chart(px.histogram(df, x="valor", nbins=30, title="Histograma de valores"), use_container_width=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Interpretar con IA - Histograma"):
            prompt = "Analiza el histograma de distribución de valores de disponibilidad de agua en Calderón."
            solicitar_interpretacion("histograma", prompt)
    with col2:
        if st.button("Limpiar interpretación - Histograma"):
            st.session_state.interpretaciones["histograma"] = ""

    if st.session_state.interpretaciones["histograma"]:
        st.info(st.session_state.interpretaciones["histograma"])

    # --- Resumen ---
    total_dias = df.shape[0]
    dias_sin_agua = df[df["valor"] == 0].shape[0]
    porcentaje_sin_agua = (dias_sin_agua / total_dias) * 100 if total_dias > 0 else 0

    fiabilidad = None
    if {"completo_mediciones", "completo_umbral"}.issubset(df.columns):
        fiabilidad = (df["completo_mediciones"] >= df["completo_umbral"]).sum() / total_dias * 100

    resumen = {
        "Total de días registrados": total_dias,
        "Días sin agua (valor = 0)": dias_sin_agua,
        "Porcentaje sin disponibilidad (%)": round(porcentaje_sin_agua, 2),
        "Fiabilidad (%)": round(fiabilidad, 2) if fiabilidad is not None else "No disponible"
    }
    st.markdown("### Resumen de indicadores")
    st.json(resumen)

with tab3:
    st.subheader("3️⃣ Análisis de archivo personalizado")

    archivo_cargado = st.file_uploader("Sube tu archivo CSV", type=["csv"])
    
    if archivo_cargado is not None:
        df_personalizado = pd.read_csv(archivo_cargado)
        
        # Mostrar datos cargados
        st.success("✅ Archivo cargado correctamente.")
        st.dataframe(df_personalizado.head())

        # Mostrar gráfica
        if "fecha" in df_personalizado.columns and "valor" in df_personalizado.columns:
            df_personalizado["fecha"] = pd.to_datetime(df_personalizado["fecha"], errors="coerce")
            st.line_chart(df_personalizado.set_index("fecha")["valor"])

            # Construir prompt de análisis
            prompt_analisis = (
                f"Aquí tienes datos de disponibilidad de agua para Calderón:\n{df_personalizado.head(30).to_string(index=False)}\n\n"
                "Por favor, proporciona un análisis técnico de la situación de sequía basándote en los datos proporcionados. "
                "Incluye observaciones, posibles causas y recomendaciones."
            )

            # Mostrar botón para interpretación con modelo seleccionado
            if st.button("🧠 Interpretar con IA"):
                modelo = st.session_state.get("modelo_seleccionado", "openai").lower()
                st.info(f"Generando análisis automático con el modelo: {modelo}...")

                try:
                    analisis_automatico = interpretar_grafica(prompt_analisis, modelo=modelo)
                    st.markdown("### 🔍 Análisis generado por IA")
                    st.write(analisis_automatico)
                except Exception as e:
                    st.error(f"❌ Error al generar el análisis con IA: {e}")
        else:
            st.warning("El archivo debe tener las columnas 'fecha' y 'valor'.")

with tab4:
    st.subheader("4️⃣ Generar Reporte PDF y Enviar por Correo")

    if "reporte_generado" not in st.session_state:
        st.session_state.reporte_generado = False

    if st.button("📄 Generar Reporte PDF"):
        with st.spinner("🚀 Generando reporte... por favor espera"):
            try:
                respuesta = requests.get("http://localhost:8000/reporte")
                if respuesta.status_code == 200:
                    with open("reporte_sequia.pdf", "wb") as f:
                        f.write(respuesta.content)
                    st.success("✅ Reporte generado exitosamente.")
                    st.session_state.reporte_generado = True
                else:
                    st.error(f"❌ Error al generar el reporte: {respuesta.text}")
            except Exception as e:
                st.error(f"❌ No se pudo conectar con el backend: {e}")

    if st.session_state.reporte_generado:
        with open("reporte_sequia.pdf", "rb") as pdf_file:
            st.download_button(
                label="📥 Descargar Reporte",
                data=pdf_file,
                file_name="reporte_sequia.pdf",
                mime="application/pdf"
            )

    st.markdown("---")

    st.markdown("### ✉️ Enviar Reporte por Correo")
    email_destinatario = st.text_input("Ingrese correo del destinatario")

    if st.button("📬 Enviar Correo"):
        if not email_destinatario:
            st.warning("⚠️ Debes ingresar un correo válido.")
        else:
            with st.spinner("🚀 Enviando correo..."):
                try:
                    payload = {"destinatario": email_destinatario}
                    respuesta = requests.post("http://localhost:8000/reporte/enviar", json=payload)
                    if respuesta.status_code == 200:
                        st.success("✅ Correo enviado exitosamente.")
                    else:
                        st.error(f"❌ Error al enviar correo: {respuesta.text}")
                except Exception as e:
                    st.error(f"❌ Error de conexión con backend: {e}")

