import pandas as pd
import pdfkit
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shutil
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import requests

# Cargar variables de entorno
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "C20-Calderón_Precipitación-Diario.csv")
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"  # Cambia "tu-modelo" por el modelo que usas

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def analizar_grafico_con_huggingface(prompt):
    payload = {"inputs": prompt}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Según el modelo, la respuesta puede variar en formato:
        # puede ser lista con dicts que contienen 'generated_text'
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()
        elif isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
        else:
            # Si es texto plano o diferente
            return str(data).strip()
    except Exception as e:
        return f"⚠️ Error al generar análisis IA Hugging Face: {e}"

def enviar_correo_con_adjunto(destinatario, asunto, cuerpo, archivo_adjunto):
    remitente = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")

    if not remitente or not password:
        print("❌ ERROR: No se encontró EMAIL_SENDER o EMAIL_PASSWORD en las variables de entorno.")
        return False

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destinatario
    msg.set_content(cuerpo)

    try:
        with open(archivo_adjunto, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(archivo_adjunto))
    except Exception as e:
        print(f"❌ Error al adjuntar archivo: {e}")
        return False

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        print("✅ Correo enviado correctamente.")
        return True
    except smtplib.SMTPAuthenticationError as e:
        error_msg = e.smtp_error.decode() if e.smtp_error else str(e)
        print(f"❌ Error de autenticación SMTP: {e.smtp_code} - {error_msg}")
        return False
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        return False

def generar_reporte_pdf(nombre_archivo="reporte_sequia.pdf", correo_destino=None):
    try:
        df = pd.read_csv(DATA_PATH, parse_dates=["fecha"])
    except Exception as e:
        print(f"❌ Error al cargar el CSV: {e}")
        return False

    total_dias = len(df)
    dias_sin_agua = len(df[df["valor"] == 0])
    porcentaje_sin_agua = round((dias_sin_agua / total_dias) * 100, 2) if total_dias > 0 else 0
    fiabilidad = 0
    if "completo_mediciones" in df.columns and "completo_umbral" in df.columns:
        fiabilidad = round((df["completo_mediciones"] >= df["completo_umbral"]).sum() / total_dias * 100, 2)
    fecha_inicio = df["fecha"].min().strftime("%Y-%m-%d")
    fecha_fin = df["fecha"].max().strftime("%Y-%m-%d")

    # 📊 Gráficos
    temp_dir = os.path.join(BASE_DIR, "temp_figs")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        df["año"] = df["fecha"].dt.year
        dias_sin_agua_por_año = df[df["valor"] == 0].groupby("año").size()

        # Gráfico 1: barras
        plt.figure(figsize=(8, 4))
        dias_sin_agua_por_año.plot(kind="bar", color="darkblue")
        plt.title("Días sin disponibilidad de agua por año")
        plt.xlabel("Año")
        plt.ylabel("Días sin agua")
        plt.tight_layout()
        grafico1_path = os.path.join(temp_dir, "dias_sin_agua_anio.png")
        plt.savefig(grafico1_path)
        plt.close()

        analisis1 = analizar_grafico_con_huggingface(
            "Analiza la siguiente información: número de días sin agua por año en la parroquia Calderón.\n"
            f"{dias_sin_agua_por_año.to_string()}"
        )

        # Gráfico 2: línea de tiempo
        plt.figure(figsize=(8, 4))
        plt.plot(df["fecha"], df["valor"], color="green")
        plt.title("Variación de disponibilidad de agua en el tiempo")
        plt.xlabel("Fecha")
        plt.ylabel("Valor indicador")
        plt.tight_layout()
        grafico2_path = os.path.join(temp_dir, "variacion_disponibilidad.png")
        plt.savefig(grafico2_path)
        plt.close()

        analisis2 = analizar_grafico_con_huggingface(
            "Analiza la siguiente serie temporal de disponibilidad de agua (valor del indicador) para Calderón.\n"
            f"{df[['fecha','valor']].tail(20).to_string(index=False)}"
        )

        grafico1_url = f"file:///{os.path.abspath(grafico1_path).replace(os.sep, '/')}"
        grafico2_url = f"file:///{os.path.abspath(grafico2_path).replace(os.sep, '/')}"

    except Exception as e:
        print(f"❌ Error generando gráficos: {e}")
        return False

    # 📄 HTML del reporte
    html = f"""<!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><title>Reporte Sequía</title></head>
    <body>
    <h1>Reporte de Sequía - Parroquia Calderón 💧</h1>
    <p><strong>Fecha:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p><strong>Período:</strong> {fecha_inicio} a {fecha_fin}</p>
    <h2>📌 Resumen</h2>
    <ul>
        <li>Total días: {total_dias}</li>
        <li>Días sin agua: {dias_sin_agua}</li>
        <li>Porcentaje sin agua: {porcentaje_sin_agua}%</li>
        <li>Fiabilidad: {fiabilidad}%</li>
    </ul>
    <h2>📈 Gráficos y Análisis</h2>

    <h3>🟦 Días sin disponibilidad de agua por año</h3>
    <img src="{grafico1_url}" width="600"/>
    <p><strong>Análisis IA:</strong> {analisis1}</p>

    <h3>🟩 Variación de disponibilidad de agua en el tiempo</h3>
    <img src="{grafico2_url}" width="600"/>
    <p><strong>Análisis IA:</strong> {analisis2}</p>

    </body>
    </html>
    """

    config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    options = {"enable-local-file-access": '', 'quiet': ''}

    try:
        pdfkit.from_string(html, nombre_archivo, configuration=config, options=options)
        print(f"✅ Reporte generado correctamente: {nombre_archivo}")
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"❌ Error al generar PDF: {e}")
        return False

    if correo_destino:
        return enviar_correo_con_adjunto(
            destinatario=correo_destino,
            asunto="Reporte de Sequía - Calderón",
            cuerpo="Adjunto el reporte generado con análisis automático de los gráficos 📊",
            archivo_adjunto=nombre_archivo
        )

    return True

# 🧪 Prueba manual
if __name__ == "__main__":
    generar_reporte_pdf(correo_destino="usuario@ejemplo.com")
