import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

remitente = os.getenv("EMAIL_SENDER")
password = os.getenv("EMAIL_PASSWORD")

print(f"Usuario: {remitente}")
print(f"Password length: {len(password) if password else 'No definido'}")

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.set_debuglevel(1)
        smtp.login(remitente, password)
    print("Login exitoso")
except Exception as e:
    print(f"Error en login SMTP: {e}")
