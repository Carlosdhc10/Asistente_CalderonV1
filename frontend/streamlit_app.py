import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

# Configuración de la app
st.set_page_config(page_title="Asistente Sequía Calderón", page_icon="💧", layout="wide")
st.title("💧 Asistente de Análisis de Sequías - Calderón")

# Ruta al archivo CSV
DATA_PATH = os.path.join("data", "C20-Calderón_Precipitación-Diario.csv")

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv(DATA_PATH, parse_dates=["fecha"])
        return df
    except Exception as e:
        st.error(f"No se pudo cargar el archivo CSV: {e}")
        return pd.DataFrame()

# --- INTERFAZ CON TABS ---
tab1, tab2 = st.tabs(["🧠 Asistente Conversacional", "📊 Análisis de Datos"])

# 1. ASISTENTE CONVERSACIONAL
with tab1:
    st.subheader("Haz preguntas sobre la sequía o el suministro de agua")
    pregunta = st.text_input("Tu pregunta:")

    if st.button("Preguntar"):
        if pregunta.strip() == "":
            st.warning("Por favor, ingresa una pregunta válida.")
        else:
            with st.spinner("Consultando al asistente..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/chatbot",
                        json={"pregunta": pregunta}
                    )
                    if response.status_code == 200:
                        respuesta = response.json().get("respuesta", "Sin respuesta.")
                        st.success("Asistente:")
                        st.write(respuesta)
                    else:
                        st.error("Error al contactar con el backend.")
                except Exception as e:
                    st.error(f"No se pudo conectar con el backend: {e}")

# 2. ANÁLISIS DE DATOS
with tab2:
    st.subheader("Explora los datos históricos del suministro de agua")

    df = cargar_datos()
    if df.empty:
        st.stop()

    # Mostrar columnas disponibles
    st.write("Columnas disponibles en el dataset:", df.columns.tolist())

    # --- Gráfico: registros por año ---
    st.markdown("### Número de registros por año")
    df["año"] = df["fecha"].dt.year
    registros_por_año = df.groupby("año").size()
    st.bar_chart(registros_por_año)

    # Línea de tiempo de valor (disponibilidad)
    st.markdown("### Variación de disponibilidad de agua a lo largo del tiempo")
    fig_line = px.line(df, x="fecha", y="valor", title="Variación temporal del indicador 'valor'")
    st.plotly_chart(fig_line, use_container_width=True)

    # Dispersión de valor sobre fecha
    st.markdown("### Dispersión de valores a lo largo del tiempo")
    fig_scatter = px.scatter(df, x="fecha", y="valor", title="Dispersión temporal del indicador 'valor'")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Histograma de valores
    st.markdown("### Distribución del indicador 'valor' (Histograma)")
    fig_hist = px.histogram(df, x="valor", nbins=30, title="Histograma de 'valor'")
    st.plotly_chart(fig_hist, use_container_width=True)

    # Mostrar tabla resumen de indicadores
    st.markdown("### Resumen de indicadores")

    total_dias = df.shape[0]
    dias_sin_agua = df[df["valor"] == 0].shape[0]
    porcentaje_sin_agua = (dias_sin_agua / total_dias) * 100 if total_dias > 0 else 0

    fiabilidad = (df["completo_mediciones"] >= df["completo_umbral"]).sum() / total_dias * 100 if total_dias > 0 else 0

    resumen = {
        "Total de días registrados": total_dias,
        "Días sin disponibilidad (valor=0)": dias_sin_agua,
        "Porcentaje sin disponibilidad (%)": round(porcentaje_sin_agua, 2),
        "Fiabilidad (%)": round(fiabilidad, 2)
    }
    st.json(resumen)

    # --- Análisis automático del comportamiento de disponibilidad ---
    st.markdown("### 🧠 Análisis automático del comportamiento de disponibilidad")

    try:
        mensaje_analisis = ""

        max_valor = df["valor"].max()
        min_valor = df["valor"].min()

        if porcentaje_sin_agua > 30:
            mensaje_analisis += f"🔴 Se observa un **alto porcentaje de días sin disponibilidad** de agua: {round(porcentaje_sin_agua, 2)}%.\n\n"

        if fiabilidad < 70:
            mensaje_analisis += f"⚠️ El nivel de **fiabilidad de los datos** es bajo: {round(fiabilidad, 2)}%. Revisa la calidad de las mediciones.\n\n"

        mensaje_analisis += f"📌 El **valor mínimo** registrado es {min_valor}, mientras que el **máximo** es {max_valor}.\n\n"

        tendencia = df.sort_values("fecha").set_index("fecha")["valor"].rolling(window=30).mean()
        if tendencia.iloc[-1] < tendencia.iloc[0]:
            mensaje_analisis += "📉 Se detecta una **tendencia decreciente** en la disponibilidad en el período observado.\n"
        else:
            mensaje_analisis += "📈 Se detecta una **tendencia creciente o estable** en la disponibilidad.\n"

        st.info(mensaje_analisis)

    except Exception as e:
        st.error(f"No se pudo generar el análisis automático: {e}")
