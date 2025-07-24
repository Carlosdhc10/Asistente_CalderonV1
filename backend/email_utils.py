import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def enviar_correo_con_adjunto(asunto, cuerpo, ruta_pdf, destinatario):
    try:
        mensaje = EmailMessage()
        mensaje["From"] = SMTP_USER
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.set_content(cuerpo)

        with open(ruta_pdf, "rb") as f:
            pdf_data = f.read()
        mensaje.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=os.path.basename(ruta_pdf))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(mensaje)
        
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
