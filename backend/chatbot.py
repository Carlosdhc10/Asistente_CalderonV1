import os
import openai
import requests
from dotenv import load_dotenv

load_dotenv()

# === API Keys ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# === OpenAI Config ===
openai.api_key = OPENAI_API_KEY

# === OpenAI GPT ===
def generar_respuesta_openai(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente técnico especializado en gestión de sequías y recursos hídricos. "
                        "Responde de manera clara, técnica y basada en datos científicos sobre la situación en Calderón."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error en la API OpenAI: {e}"

# === Hugging Face Zephyr 7B ===
def generar_respuesta_zephyr(prompt: str) -> str:
    try:
        url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }

        # Formato de entrada estilo chat
        data = {
            "inputs": (
                "<|system|>"
                "Eres un experto asistente técnico en gestión de sequías y recursos hídricos. "
                "Tu tarea es responder de manera clara, detallada y científica, enfocándote en la situación del suministro de agua en la parroquia de Calderón, Quito, Ecuador. "
                "Proporciona respuestas basadas en datos y análisis científicos, evitando conjeturas no fundamentadas."
                "<|user|>"
                f"{prompt}"
                "<|assistant|>"
            ),
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.4,
                "do_sample": True,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            generated_text = result[0]["generated_text"]
            # Extraer solo la respuesta después del <|assistant|>
            respuesta = generated_text.split("<|assistant|>")[-1].strip()
            return respuesta or "Sin respuesta."
        else:
            return f"Error Hugging Face API: {response.status_code} {response.text}"
    except Exception as e:
        return f"Error en la API Hugging Face: {e}"

# === Orquestador ===
def responder_pregunta(pregunta: str, modelo: str = "openai") -> str:
    modelo = modelo.lower()
    if modelo == "zephyr":
        return generar_respuesta_zephyr(pregunta)
    else:
        return generar_respuesta_openai(pregunta)
