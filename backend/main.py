from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.chatbot import responder_pregunta

app = FastAPI(title="Asistente Sequía Calderón")

# Middleware CORS (restringe en producción si es necesario)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar esto a origenes específicos en producción
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta raíz de prueba
@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente"}

# Modelo para la entrada del chatbot
class PreguntaInput(BaseModel):
    pregunta: str

# Endpoint del chatbot
@app.post("/chatbot")
def chat_endpoint(input: PreguntaInput):
    respuesta = responder_pregunta(input.pregunta)
    return {"respuesta": respuesta}
