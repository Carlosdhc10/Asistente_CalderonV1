import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import time
import re  # import para validar email

# Configuración de la app
st.set_page_config(page_title="Asistente Sequía Calderón", page_icon="💧", layout="wide")
st.title("Asistente de Análisis de Sequías - Calderón")

DATA_PATH = os.path.join("data", "C20-Calderón_Precipitación-Diario.csv")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv(DATA_PATH, parse_dates=["fecha"])
        return df
    except Exception as e:
        st.error(f"No se pudo cargar el archivo CSV: {e}")
        return pd.DataFrame()

tab1, tab2, tab3 = st.tabs(["Asistente Conversacional", "Análisis de Datos", "Subir tus propios datos"])

with tab1:
    st.subheader("Haz preguntas sobre la sequía o el suministro de agua")
    pregunta = st.text_input("Tu pregunta:")

    if st.button("Preguntar"):
        if not pregunta.strip():
            st.warning("Por favor, ingresa una pregunta válida.")
        else:
            with st.spinner("Consultando al asistente..."):
                try:
                    response = requests.post("http://localhost:8000/chatbot", json={"pregunta": pregunta})
                    if response.status_code == 200:
                        respuesta = response.json().get("respuesta", "Sin respuesta.")
                        st.success("Asistente:")
                        st.write(respuesta)
                    else:
                        st.error("Error al contactar con el backend.")
                except Exception as e:
                    st.error(f"No se pudo conectar con el backend: {e}")

with tab2:
    st.subheader("Explora los datos históricos del suministro de agua")

    df = cargar_datos()
    if df.empty:
        st.stop()

    st.write("Columnas disponibles en el dataset:", df.columns.tolist())

    if "fecha" not in df.columns or "valor" not in df.columns:
        st.error("El archivo debe contener las columnas 'fecha' y 'valor'.")
        st.stop()

    df["año"] = df["fecha"].dt.year

    st.markdown("### Número de registros por año")
    st.bar_chart(df.groupby("año").size())

    st.markdown("### Variación de disponibilidad de agua a lo largo del tiempo")
    st.plotly_chart(px.line(df, x="fecha", y="valor", title="Tendencia de 'valor'"), use_container_width=True)

    st.markdown("### Dispersión de valores en el tiempo")
    st.plotly_chart(px.scatter(df, x="fecha", y="valor", title="Dispersión del indicador 'valor'"), use_container_width=True)

    st.markdown("### Distribución del indicador 'valor' (Histograma)")
    st.plotly_chart(px.histogram(df, x="valor", nbins=30), use_container_width=True)

    st.markdown("### Resumen de indicadores")
    total_dias = df.shape[0]
    dias_sin_agua = df[df["valor"] == 0].shape[0]
    porcentaje_sin_agua = (dias_sin_agua / total_dias) * 100 if total_dias > 0 else 0

    if "completo_mediciones" in df.columns and "completo_umbral" in df.columns:
        fiabilidad = (df["completo_mediciones"] >= df["completo_umbral"]).sum() / total_dias * 100
    else:
        fiabilidad = None

    resumen = {
        "Total de días registrados": total_dias,
        "Días sin agua (valor = 0)": dias_sin_agua,
        "Porcentaje sin disponibilidad (%)": round(porcentaje_sin_agua, 2),
        "Fiabilidad (%)": round(fiabilidad, 2) if fiabilidad is not None else "No disponible"
    }
    st.json(resumen)

    st.markdown("### Generar y descargar reporte PDF")
    if st.button("Generar reporte"):
        progreso = st.progress(0)
        status_text = st.empty()
        for i in range(100):
            time.sleep(0.02)  # Simula progreso
            progreso.progress(i + 1)
            status_text.text(f"Generando reporte... {i + 1}%")
        
        status_text.text("Solicitando reporte al backend...")
        try:
            response = requests.get("http://localhost:8000/reporte")
            if response.status_code == 200:
                file_path = f"reporte_sequia_{datetime.now().date()}.pdf"
                with open(file_path, "wb") as f:
                    f.write(response.content)
                st.success("Reporte generado correctamente.")
                with open(file_path, "rb") as f:
                    st.download_button("Descargar Reporte PDF", f, file_name=file_path, mime="application/pdf")
            else:
                st.error("No se pudo generar el reporte.")
        except Exception as e:
            st.error(f"Error: {e}")

    # Formulario para enviar correo con reporte
    st.markdown("### 📧 Enviar reporte de sequía por correo")

    with st.form("form_envio_reporte"):
        correo_destino = st.text_input("Ingresa el correo del destinatario")
        enviar = st.form_submit_button("Enviar reporte")

        email_pattern = r"[^@]+@[^@]+\.[^@]+"
        if enviar:
            if not correo_destino or not re.match(email_pattern, correo_destino):
                st.warning("Por favor ingresa un correo válido.")
            else:
                progreso_envio = st.progress(0, text="Iniciando generación del reporte...")
                try:
                    # Simula progreso de generación
                    for i in range(40):
                        time.sleep(0.02)
                        progreso_envio.progress(i + 1, text=f"Generando reporte... {i + 1}%")

                    response = requests.post(
                        "http://localhost:8000/reporte/enviar",
                        json={"destinatario": correo_destino}
                    )

                    # Simula progreso de envío
                    for i in range(40, 100):
                        time.sleep(0.02)
                        progreso_envio.progress(i + 1, text=f"Enviando correo... {i + 1}%")

                    if response.status_code == 200:
                        progreso_envio.progress(100, text="Reporte enviado con éxito.")
                        st.success("✅ Correo enviado correctamente.")
                    else:
                        progreso_envio.empty()
                        st.error(f"❌ Error al enviar el reporte: {response.text}")
                except Exception as e:
                    progreso_envio.empty()
                    st.error(f"❌ No se pudo conectar al backend: {e}")

with tab3:
    st.subheader("Sube tu propio archivo CSV")

    uploaded_file = st.file_uploader("Selecciona un CSV con columnas 'fecha' y 'valor':", type=["csv"])

    if uploaded_file:
        try:
            df_custom = pd.read_csv(uploaded_file, parse_dates=["fecha"])
            if "fecha" not in df_custom.columns or "valor" not in df_custom.columns:
                st.error("El archivo debe contener 'fecha' y 'valor'.")
                st.stop()

            df_custom["año"] = df_custom["fecha"].dt.year
            st.success("Archivo cargado correctamente.")

            st.markdown("### Registros por año")
            st.bar_chart(df_custom.groupby("año").size())

            st.markdown("### Variación temporal de 'valor'")
            st.plotly_chart(px.line(df_custom, x="fecha", y="valor", title="Tendencia"), use_container_width=True)

            st.markdown("### Histograma de valores")
            st.plotly_chart(px.histogram(df_custom, x="valor", nbins=30), use_container_width=True)

            total_dias = df_custom.shape[0]
            dias_sin_agua = df_custom[df_custom["valor"] == 0].shape[0]
            porcentaje_sin_agua = (dias_sin_agua / total_dias) * 100 if total_dias > 0 else 0

            if "completo_mediciones" in df_custom.columns and "completo_umbral" in df_custom.columns:
                fiabilidad = (df_custom["completo_mediciones"] >= df_custom["completo_umbral"]).sum() / total_dias * 100
            else:
                fiabilidad = None

            resumen = {
                "Total días": total_dias,
                "Días sin agua": dias_sin_agua,
                "Porcentaje sin disponibilidad": round(porcentaje_sin_agua, 2),
                "Fiabilidad (%)": round(fiabilidad, 2) if fiabilidad is not None else "No disponible"
            }

            st.markdown("### Resumen")
            st.json(resumen)

        except Exception as e:
            st.error(f"No se pudo analizar el archivo: {e}")
    else:
        st.info("Sube un archivo para comenzar el análisis.")
