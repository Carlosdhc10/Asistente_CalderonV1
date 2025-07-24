from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from backend.chatbot import responder_pregunta
from backend.generar_reporte import generar_reporte_pdf, enviar_correo_con_adjunto
from fastapi.responses import FileResponse

app = FastAPI(title="Asistente Sequía Calderón")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción ajustar dominios
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente"}

# 👇 Ahora aceptamos también el modelo a usar
class PreguntaInput(BaseModel):
    pregunta: str
    modelo: str = "openai"  # Por defecto usará OpenAI, pero puede cambiarse a huggingface

@app.post("/chatbot")
def chat_endpoint(input: PreguntaInput):
    try:
        respuesta = responder_pregunta(input.pregunta, modelo=input.modelo)
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en chatbot: {e}")

@app.get("/reporte")
def descargar_reporte():
    nombre_pdf = "reporte_sequia.pdf"
    exito = generar_reporte_pdf(nombre_pdf)
    if not exito:
        raise HTTPException(status_code=500, detail="Error al generar el reporte")
    return FileResponse(path=nombre_pdf, filename=nombre_pdf, media_type='application/pdf')

class EmailRequest(BaseModel):
    destinatario: EmailStr

@app.post("/reporte/enviar")
def generar_y_enviar_reporte(request: EmailRequest):
    nombre_pdf = "reporte_sequia.pdf"
    exito = generar_reporte_pdf(nombre_pdf)
    if not exito:
        raise HTTPException(status_code=500, detail="No se pudo generar el PDF.")

    enviado = enviar_correo_con_adjunto(
        destinatario=request.destinatario,
        asunto="Reporte de Sequía - Calderón",
        cuerpo="Adjunto encontrarás el reporte de sequía para el sector de Calderón.",
        archivo_adjunto=nombre_pdf
    )

    if not enviado:
        raise HTTPException(status_code=500, detail="No se pudo enviar el correo.")
    
    return {"mensaje": "Correo enviado correctamente."}
