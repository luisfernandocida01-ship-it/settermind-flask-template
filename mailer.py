import html
import os
from urllib.parse import urlencode
import resend

def send_welcome_email(to_email: str, buyer_name: str, raw_api_key: str) -> object:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY no está configurada.")

    resend.api_key = api_key

    sender_email = os.environ.get(
        "SENDER_EMAIL",
        "SetterMind AI <servicioalcliente@mentesalmercado.online>",
    )
    frontend_url = os.environ.get(
        "FRONTEND_URL",
        "https://settermind.mentesalmercado.online",
    ).strip().rstrip("/")
    if not frontend_url:
        raise RuntimeError("FRONTEND_URL no puede estar vacío.")

    magic_link = f"{frontend_url}/register?{urlencode({'key': raw_api_key})}"
    escaped_name = html.escape(buyer_name or "Setter")
    escaped_key = html.escape(raw_api_key)
    escaped_link = html.escape(magic_link, quote=True)

    html_content = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="es">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Acceso SetterMind AI</title>
</head>
<body style="margin: 0; padding: 0; background-color: #070B11; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="#070B11" style="background-color: #070B11; table-layout: fixed;">
    <tr>
      <td align="center" style="padding: 40px 10px;">
        <!-- Tarjeta Principal -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #111A28; border: 1px solid #1E2D42; border-radius: 16px; overflow: hidden;" bgcolor="#111A28">
          <tr>
            <td align="center" style="padding: 40px 30px;">
              
              <!-- Badge Logo 'M' -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="60" height="60" bgcolor="#0E2A47" style="background-color: #0E2A47; border: 2px solid #D4AF37; border-radius: 14px; margin-bottom: 24px;">
                <tr>
                  <td align="center" valign="middle" style="color: #F3C969; font-size: 28px; font-weight: bold; font-family: Arial, sans-serif; height: 60px;">
                    M
                  </td>
                </tr>
              </table>

              <!-- Titular -->
              <h1 style="color: #FFFFFF !important; font-size: 24px; font-weight: bold; margin: 0 0 16px 0; text-align: center; font-family: Arial, sans-serif;">
                ¡Bienvenido a SetterMind AI!
              </h1>

              <!-- Saludo y Explicación -->
              <p style="color: #94A3B8 !important; font-size: 15px; line-height: 24px; margin: 0 0 24px 0; text-align: center; font-family: Arial, sans-serif;">
                Hola <strong style="color: #FFFFFF !important;">{escaped_name}</strong>, tu cuenta de inteligencia y prospección consultiva ha sido aprovisionada con éxito en Hotmart.
              </p>

              <p style="color: #94A3B8 !important; font-size: 14px; line-height: 22px; margin: 0 0 28px 0; text-align: center; font-family: Arial, sans-serif;">
                Para ingresar al instante sin necesidad de recordar contraseñas, utiliza tu enlace de acceso directo seguro:
              </p>

              <!-- Botón Autologin -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto 30px auto;">
                <tr>
                  <td align="center" bgcolor="#0284C7" style="border-radius: 10px; background-color: #0284C7;">
                    <a href="{escaped_link}" target="_blank" style="display: inline-block; padding: 16px 36px; font-family: Arial, sans-serif; font-size: 15px; font-weight: bold; color: #FFFFFF !important; text-decoration: none; border-radius: 10px;">
                      Ingresar a SetterMind AI (Autologin)
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Respaldo de Enlace Texto -->
              <p style="color: #64748B !important; font-size: 12px; margin: 0 0 8px 0; text-align: left; font-family: Arial, sans-serif;">
                Si el botón no abre automáticamente, copia y pega este enlace en tu navegador:
              </p>
              <p style="margin: 0 0 30px 0; text-align: left;">
                <a href="{escaped_link}" target="_blank" style="color: #38BDF8 !important; font-size: 12px; word-break: break-all; text-decoration: underline; font-family: Arial, sans-serif;">
                  {escaped_link}
                </a>
              </p>

              <!-- Caja de Clave de Respaldo -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="#070C14" style="background-color: #070C14; border: 1px dashed #1E2D42; border-radius: 10px; margin-bottom: 28px;">
                <tr>
                  <td style="padding: 18px 20px;">
                    <p style="color: #94A3B8 !important; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 0 0 8px 0; text-transform: uppercase; font-family: Arial, sans-serif;">
                      CREDENCIAL DE RESPALDO (API KEY)
                    </p>
                    <p style="color: #38BDF8 !important; font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; word-break: break-all; margin: 0 0 8px 0;">
                      {escaped_key}
                    </p>
                    <p style="color: #64748B !important; font-size: 11px; margin: 0; line-height: 16px; font-family: Arial, sans-serif;">
                      Guarda esta clave. Puedes pegarla manualmente si abres la app en un navegador privado o un dispositivo nuevo.
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Pie de Soporte -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top: 1px solid #1E2D42;">
                <tr>
                  <td align="center" style="padding-top: 24px;">
                    <p style="color: #94A3B8 !important; font-size: 13px; font-weight: bold; margin: 0 0 4px 0; font-family: Arial, sans-serif;">
                      Mentes al Mercado · División Software
                    </p>
                    <p style="color: #64748B !important; font-size: 11px; margin: 0; font-family: Arial, sans-serif;">
                      Soporte oficial: servicioalcliente@mentesalmercado.online
                    </p>
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
</html>"""

    text_content = (
        f"¡Bienvenido a SetterMind AI, {buyer_name}!\n\n"
        f"Tu cuenta ha sido aprovisionada con éxito.\n"
        f"Ingresa directamente aquí: {magic_link}\n\n"
        f"Tu clave de respaldo: {raw_api_key}\n\n"
        f"Mentes al Mercado · Soporte: servicioalcliente@mentesalmercado.online"
    )

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": "Tu acceso y clave de licencia a SetterMind AI",
        "html": html_content,
        "text": text_content,
    }

    return resend.Emails.send(params)
