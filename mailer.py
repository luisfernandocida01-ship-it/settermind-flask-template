# mailer.py
import os
import resend

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get(
    "SENDER_EMAIL",
    "SetterMind AI <servicioalcliente@mentesalmercado.online>"
)
APP_URL = os.environ.get(
    "FRONTEND_URL",
    "https://settermind.mentesalmercado.online"
)

def send_welcome_email(to_email: str, buyer_name: str, raw_api_key: str):
    """
    Envía el correo de bienvenida transaccional con enlace directo al registro
    y credenciales de respaldo para SetterMind AI.
    """
    if not RESEND_API_KEY:
        print("[MAILER WARNING] RESEND_API_KEY no configurada. Correo omitido en desarrollo local.")
        return None

    resend.api_key = RESEND_API_KEY
    encoded_key = str(raw_api_key).strip()
    magic_link = f"{APP_URL}/register?key={encoded_key}"

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="background-color: #0B111A; color: #F1F5F9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 30px 15px;">
  <div style="max-width: 580px; margin: 0 auto; background-color: #111A28; border: 1px solid #1E2D42; border-radius: 14px; padding: 35px 25px; text-align: center;">
    
    <div style="display: inline-block; width: 55px; height: 55px; line-height: 55px; border-radius: 12px; background: #0E2A47; border: 2px solid #D4AF37; color: #F3C969; font-weight: 800; font-size: 26px; margin-bottom: 20px;">
      M
    </div>
    
    <h1 style="color: #FFFFFF; font-size: 24px; margin: 0 0 10px 0;">¡Bienvenido a SetterMind AI!</h1>
    <p style="color: #CBD5E1; font-size: 15px; line-height: 1.5; margin: 0 0 20px 0;">
      Hola <strong>{buyer_name}</strong>, tu cuenta de inteligencia y prospección consultiva ha sido aprovisionada con éxito en Hotmart.
    </p>
    
    <p style="color: #CBD5E1; font-size: 15px; line-height: 1.5; margin: 0 0 20px 0;">
      Para ingresar al instante sin necesidad de recordar contraseñas, utiliza tu enlace de acceso directo seguro:
    </p>
    
    <div style="margin: 25px 0;">
      <a href="{magic_link}" target="_blank" style="background-color: #0284C7; color: #FFFFFF !important; text-decoration: none; font-weight: bold; font-size: 16px; padding: 14px 28px; border-radius: 8px; display: inline-block; border: 1px solid #38BDF8;">
        Ingresar a SetterMind AI (Autologin)
      </a>
    </div>

    <p style="font-size: 12px; color: #64748B; margin-top: 10px;">
      Si el botón no abre automáticamente, copia y pega este enlace en tu navegador:<br/>
      <a href="{magic_link}" target="_blank" style="color: #38BDF8; word-break: break-all; font-size: 11px;">{magic_link}</a>
    </p>

    <div style="background-color: #06090E; border: 1px dashed #1E2D42; border-radius: 8px; padding: 15px; text-align: left; margin: 25px 0;">
      <p style="color: #94A3B8; font-size: 11px; margin-bottom: 6px; text-transform: uppercase; font-weight: 700;">Credencial de Respaldo (API Key)</p>
      <div style="font-family: monospace; color: #38BDF8; font-size: 13px; word-break: break-all;">{raw_api_key}</div>
      <p style="color: #64748B; font-size: 11px; margin-top: 6px; margin-bottom: 0;">Guarda esta clave. Puedes pegarla manualmente si abres la app en un navegador privado o un dispositivo nuevo.</p>
    </div>

    <div style="border-top: 1px solid #1E2D42; padding-top: 18px; color: #64748B; font-size: 12px;">
      <p style="margin-bottom: 5px;">Mentes al Mercado • División Software</p>
      <span>Soporte oficial: servicioalcliente@mentesalmercado.online</span>
    </div>

  </div>
</body>
</html>
"""

    params = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": "Tu acceso y clave de licencia a SetterMind AI",
        "html": html_content
    }

    try:
        email_response = resend.Emails.send(params)
        print(f"[MAILER SUCCESS] Correo enviado a {to_email}: {email_response}")
        return email_response
    except Exception as e:
        print(f"[MAILER ERROR] Falló el envío de correo a {to_email}: {e}")
        return None