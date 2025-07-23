import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd

# Cargar variables de entorno (incluye API key)
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Configurar Gemini
genai.configure(api_key=API_KEY)
modelo = genai.GenerativeModel("gemini-1.5-pro")

# Ruta CSV
CSV_PATH = os.path.join("data", "C20-Calderón_Precipitación-Diario.csv")

# Función para cargar datos (solo una muestra resumida para contexto)
def cargar_contexto_csv():
    try:
        df = pd.read_csv(CSV_PATH, parse_dates=["fecha"])
        resumen = df.describe(include="all").to_string()
        return f"Datos históricos de disponibilidad de agua en Calderón:\n{resumen}"
    except Exception as e:
        return f"No se pudo cargar los datos: {e}"

# Preparar contexto base
contexto_base = """
Calderón es una parroquia de Quito con variabilidad en el suministro de agua.
Responde en español, con precisión y claridad.
"""

# Combina contexto + CSV
contexto_total = contexto_base + "\n\n" + cargar_contexto_csv()

# Función principal de respuesta
def responder_pregunta(pregunta: str) -> str:
    try:
        response = modelo.generate_content([contexto_total, f"Pregunta: {pregunta}"])
        return response.text.strip()
    except Exception as e:
        return f"Ocurrió un error con Gemini: {e}"
