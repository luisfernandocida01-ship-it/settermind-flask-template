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

# mailer.py
import os
import resend

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get(
    "SENDER_EMAIL",
    "SetterMind AI <servicioalcliente@mentesalmercado.online>"
)

RAW_APP_URL = os.environ.get(
    "FRONTEND_URL",
    "https://settermind.mentesalmercado.online"
)
APP_URL = RAW_APP_URL.replace("[", "").replace("]", "").strip().rstrip("/")


def send_welcome_email(to_email: str, buyer_name: str, raw_api_key: str):
    if not RESEND_API_KEY:
        print("[MAILER WARNING] RESEND_API_KEY no configurada.")
        return None

    resend.api_key = RESEND_API_KEY
    clean_key = str(raw_api_key).replace("[", "").replace("]", "").strip()
    magic_link = f"{APP_URL}/register?key={clean_key}"

    html_content = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SetterMind AI</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0B111A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0B111A; padding: 30px 10px;">
    <tr>
      <td align="center">
        <!-- Tarjeta Principal -->
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #111A28; border: 1px solid #1E2D42; border-radius: 14px; padding: 35px 25px; text-align: center;">
          <tr>
            <td align="center">
              
              <!-- Badge M -->
              <table border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                <tr>
                  <td align="center" style="width: 55px; height: 55px; background-color: #0E2A47; border: 2px solid #D4AF37; border-radius: 12px; color: #F3C969; font-weight: 800; font-size: 26px;">
                    M
                  </td>
                </tr>
              </table>

              <!-- Titulo -->
              <h1 style="color: #FFFFFF; font-size: 24px; margin: 0 0 12px 0; font-weight: 700;">¡Bienvenido a SetterMind AI!</h1>
              
              <!-- Mensaje -->
              <p style="color: #CBD5E1; font-size: 15px; line-height: 1.5; margin: 0 0 16px 0;">
                Hola <strong style="color: #FFFFFF;">{buyer_name}</strong>, tu cuenta de inteligencia y prospección consultiva ha sido aprovisionada con éxito en Hotmart.
              </p>
              
              <p style="color: #CBD5E1; font-size: 15px; line-height: 1.5; margin: 0 0 25px 0;">
                Para ingresar al instante sin necesidad de recordar contraseñas, utiliza tu enlace de acceso directo seguro:
              </p>

              <!-- Botón Activo Centrado -->
              <table border="0" cellpadding="0" cellspacing="0" style="margin: 20px auto 25px auto;">
                <tr>
                  <td align="center" style="border-radius: 8px; background-color: #0284C7;">
                    <a href="{magic_link}" target="_blank" style="font-size: 15px; font-weight: bold; color: #FFFFFF !important; text-decoration: none; padding: 14px 28px; border-radius: 8px; display: inline-block; border: 1px solid #38BDF8;">
                      Ingresar a SetterMind AI (Autologin)
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Enlace alternativo -->
              <p style="font-size: 12px; color: #64748B; margin: 0 0 8px 0;">
                Si el botón no abre automáticamente, copia y pega este enlace en tu navegador:
              </p>
              <p style="margin: 0 0 25px 0;">
                <a href="{magic_link}" target="_blank" style="color: #38BDF8; word-break: break-all; font-size: 11px; text-decoration: underline;">{magic_link}</a>
              </p>

              <!-- Caja de Credencial -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #06090E; border: 1px dashed #1E2D42; border-radius: 8px; margin-bottom: 25px;">
                <tr>
                  <td style="padding: 15px; text-align: left;">
                    <p style="color: #94A3B8; font-size: 11px; margin: 0 0 6px 0; text-transform: uppercase; font-weight: 700;">Credencial de Respaldo (API Key)</p>
                    <div style="font-family: monospace; color: #38BDF8; font-size: 13px; word-break: break-all;">{clean_key}</div>
                    <p style="color: #64748B; font-size: 11px; margin: 6px 0 0 0;">Guarda esta clave. Puedes pegarla manualmente si abres la app en un navegador privado o un dispositivo nuevo.</p>
                  </td>
                </tr>
              </table>

              <!-- Footer -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top: 1px solid #1E2D42;">
                <tr>
                  <td align="center" style="padding-top: 18px; color: #64748B; font-size: 12px;">
                    <p style="margin: 0 0 4px 0;">Mentes al Mercado • División Software</p>
                    <span style="color: #64748B;">Soporte oficial: servicioalcliente@mentesalmercado.online</span>
                  </td>
                </tr>
              </table>

            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    params = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": "Tu acceso y clave de licencia a SetterMind AI",
        "html": html_content,
    }

    try:
        email_response = resend.Emails.send(params)
        print(f"[MAILER SUCCESS] Correo enviado a {to_email}: {email_response}")
        return email_response
    except Exception as e:
        print(f"[MAILER ERROR] Falló el envío de correo a {to_email}: {e}")
        return None