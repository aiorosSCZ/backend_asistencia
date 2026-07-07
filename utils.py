import smtplib
from email.message import EmailMessage
import os
import json
import urllib.request
from typing import Optional

# Configuración de credenciales SMTP (Ejemplo usando Gmail)
# En producción, estas variables deben venir de un archivo .env
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "tu_correo@gmail.com") 
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "tu_contraseña_de_aplicacion")

def send_email_via_brevo(destinatario: str, subject: str, html_content: str, text_content: str = None) -> bool:
    """
    Envía un correo electrónico utilizando la API REST de Brevo (HTTP).
    """
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        print("[DEBUG EMAIL] Brevo API Key no configurada.", flush=True)
        return False
        
    sender_email = os.getenv("SMTP_USER", "asiscar.asistente@gmail.com")
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {"name": "AsisCar", "email": sender_email},
        "to": [{"email": destinatario}],
        "subject": subject,
        "htmlContent": html_content
    }
    if text_content:
        payload["textContent"] = text_content
        
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print(f"[DEBUG EMAIL] Correo enviado exitosamente a {destinatario} vía Brevo API. Respuesta: {res_body}", flush=True)
            return True
    except Exception as e:
        print(f"[DEBUG EMAIL] Error enviando correo vía Brevo API: {e}", flush=True)
        return False

def send_approval_email(destinatario: str, nombre_taller: str):
    """
    Envía un correo electrónico al taller notificando que su cuenta ha sido aprobada.
    """
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #4f46e5; color: white; padding: 20px; text-align: center;">
                    <h2>¡Bienvenido a AsisCar!</h2>
                </div>
                <div style="padding: 30px;">
                    <p>Hola <strong>{nombre_taller}</strong>,</p>
                    <p>Nos complace informarte que hemos revisado tus documentos y tu cuenta ha sido <strong>aprobada exitosamente</strong>.</p>
                    <p>A partir de este momento, tu Dashboard Operativo ha sido desbloqueado. Ya puedes:</p>
                    <ul>
                        <li>Recibir alertas de emergencias en tiempo real.</li>
                        <li>Crear cuentas para tus mecánicos.</li>
                        <li>Empezar a generar ingresos.</li>
                    </ul>
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://asiscar.netlify.app/login" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Acceder a mi Dashboard</a>
                    </div>
                </div>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                    Este es un mensaje automático, por favor no respondas a este correo.
                </div>
            </div>
        </body>
    </html>
    """
    text_content = "Tu taller ha sido aprobado. Inicia sesión para acceder al dashboard."

    # Intentar Brevo primero
    if os.getenv("BREVO_API_KEY"):
        print(f"[DEBUG EMAIL] Intentando enviar aprobación a {destinatario} vía Brevo API...", flush=True)
        success = send_email_via_brevo(destinatario, '¡Tu Taller ha sido Aprobado! - AsisCar', html_content, text_content)
        if success:
            return True
        print("[DEBUG EMAIL] Brevo API falló, reintentando con SMTP...", flush=True)

    # Fallback SMTP
    smtp_user = os.getenv("SMTP_USER", "tu_correo@gmail.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "tu_contraseña_de_aplicacion")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    print(f"[DEBUG EMAIL] Iniciando envío de aprobación SMTP a {destinatario} usando servidor {smtp_server}:{smtp_port}. Usuario: {smtp_user}", flush=True)

    msg = EmailMessage()
    msg['Subject'] = '¡Tu Taller ha sido Aprobado! - AsisCar'
    msg['From'] = smtp_user
    msg['To'] = destinatario
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype='html')

    try:
        if smtp_user and smtp_password and smtp_user != "tu_correo@gmail.com":
            if smtp_port == 465:
                print(f"[DEBUG EMAIL] Conectando por SMTP_SSL a {smtp_server}:{smtp_port}...", flush=True)
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            else:
                print(f"[DEBUG EMAIL] Conectando por SMTP standard + STARTTLS a {smtp_server}:{smtp_port}...", flush=True)
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            print(f"[DEBUG EMAIL] Correo de aprobación enviado exitosamente a {destinatario} (SMTP)", flush=True)
        else:
            print(f"[DEBUG EMAIL] SIMULACIÓN: Correo de aprobación enviado exitosamente a {destinatario}", flush=True)
        return True
    except Exception as e:
        print(f"[DEBUG EMAIL] Error enviando correo: {e}", flush=True)
        return False

def send_reset_password_email(destinatario: str, token: str):
    """
    Envía un correo electrónico con el código de verificación para restablecer la contraseña.
    """
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #4f46e5; color: white; padding: 20px; text-align: center;">
                    <h2>Recuperación de Contraseña</h2>
                </div>
                <div style="padding: 30px;">
                    <p>Hola,</p>
                    <p>Has solicitado restablecer tu contraseña en la plataforma AsisCar.</p>
                    <p>Utiliza el siguiente código de verificación para continuar con el proceso:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="background-color: #f3f4f6; color: #4f46e5; font-size: 32px; font-weight: bold; letter-spacing: 5px; padding: 10px 20px; border-radius: 8px; border: 1px dashed #4f46e5;">{token}</span>
                    </div>
                    <p>Este código es válido por 15 minutos. Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>
                </div>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                    Este es un mensaje automático, por favor no respondas a este correo.
                </div>
            </div>
        </body>
    </html>
    """
    text_content = f"Tu código de recuperación es: {token}"

    # Intentar Brevo primero
    if os.getenv("BREVO_API_KEY"):
        print(f"[DEBUG EMAIL] Intentando enviar recuperación a {destinatario} vía Brevo API...", flush=True)
        success = send_email_via_brevo(destinatario, 'Código de Recuperación de Contraseña - AsisCar', html_content, text_content)
        if success:
            return True
        print("[DEBUG EMAIL] Brevo API falló, reintentando con SMTP...", flush=True)

    # Fallback SMTP
    smtp_user = os.getenv("SMTP_USER", "tu_correo@gmail.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "tu_contraseña_de_aplicacion")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    print(f"[DEBUG EMAIL] Iniciando envío de recuperación SMTP a {destinatario} usando servidor {smtp_server}:{smtp_port}. Usuario: {smtp_user}", flush=True)

    msg = EmailMessage()
    msg['Subject'] = 'Código de Recuperación de Contraseña - AsisCar'
    msg['From'] = smtp_user
    msg['To'] = destinatario
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype='html')

    try:
        if smtp_user and smtp_password and smtp_user != "tu_correo@gmail.com":
            if smtp_port == 465:
                print(f"[DEBUG EMAIL] Conectando por SMTP_SSL a {smtp_server}:{smtp_port}...", flush=True)
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            else:
                print(f"[DEBUG EMAIL] Conectando por SMTP standard + STARTTLS a {smtp_server}:{smtp_port}...", flush=True)
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            print(f"[DEBUG EMAIL] Correo de recuperación enviado exitosamente a {destinatario} (SMTP)", flush=True)
        else:
            print(f"[DEBUG EMAIL] SIMULACIÓN: Correo de recuperación enviado a {destinatario}. Token: {token}", flush=True)
        return True
    except Exception as e:
        print(f"[DEBUG EMAIL] Error enviando correo de recuperación: {e}", flush=True)
        return False



# --- JWT HELPER FUNCTIONS ---
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-for-asiscar-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

