import html
import os
import time
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
    timestamp_mark = str(int(time.time()))[-4:]

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Acceso SetterMind AI</title>
</head>
<body style="margin:0; padding:20px 0; background-color:#0b111a; font-family:Arial, Helvetica, sans-serif;">
  <center>
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:580px; width:100%; background-color:#111a28; border:1px solid #1e2d42; border-radius:14px; text-align:center;">
      <tr>
        <td style="padding:36px 28px;">
          <!-- Logo M -->
          <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin:0 auto 20px auto; width:52px; height:52px; background-color:#0e2a47; border:2px solid #d4af37; border-radius:12px;">
            <tr>
              <td align="center" valign="middle" style="color:#f3c969; font-size:26px; font-weight:bold; font-family:Arial, sans-serif;">
                M
              </td>
            </tr>
          </table>

          <h1 style="color:#ffffff !important; font-size:22px; font-weight:bold; margin:0 0 16px 0;">
            ¡Bienvenido a SetterMind AI!
          </h1>

          <p style="color:#cbd5e1 !important; font-size:14px; line-height:22px; margin:0 0 20px 0;">
            Hola <strong style="color:#ffffff !important;">{escaped_name}</strong>, tu cuenta de inteligencia y prospección consultiva ha sido aprovisionada con éxito en Hotmart.
          </p>

          <p style="color:#94a3b8 !important; font-size:13px; line-height:20px; margin:0 0 26px 0;">
            Para ingresar al instante sin necesidad de recordar contraseñas, utiliza tu enlace de acceso directo seguro:
          </p>

          <!-- Boton Autologin -->
          <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin:0 auto 26px auto;">
            <tr>
              <td align="center" style="background-color:#0284c7; border-radius:8px;">
                <a href="{escaped_link}" target="_blank" style="display:inline-block; padding:14px 32px; font-family:Arial, sans-serif; font-size:14px; font-weight:bold; color:#ffffff !important; text-decoration:none; border-radius:8px;">
                  Ingresar a SetterMind AI (Autologin)
                </a>
              </td>
            </tr>
          </table>

          <!-- Respaldo Link -->
          <p style="color:#64748b !important; font-size:12px; margin:0 0 6px 0; text-align:left;">
            Si el botón no abre automáticamente, copia este enlace en tu navegador:
          </p>
          <p style="margin:0 0 26px 0; text-align:left;">
            <a href="{escaped_link}" target="_blank" style="color:#38bdf8 !important; font-size:12px; word-break:break-all; text-decoration:underline;">
              {escaped_link}
            </a>
          </p>

          <!-- Clave en tabla -->
          <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#0c1524; border:1px dashed #1e2d42; border-radius:8px; margin-bottom:24px;">
            <tr>
              <td style="padding:14px 16px; text-align:left;">
                <span style="color:#94a3b8 !important; font-size:10px; font-weight:bold; letter-spacing:1px; display:block; margin-bottom:6px;">
                  CREDENCIAL DE RESPALDO (API KEY)
                </span>
                <span style="color:#38bdf8 !important; font-family:monospace; font-size:12px; font-weight:bold; word-break:break-all; display:block; margin-bottom:6px;">
                  {escaped_key}
                </span>
                <span style="color:#64748b !important; font-size:11px; display:block; line-height:15px;">
                  Guarda esta clave. Puedes pegarla manualmente si abres la app en un navegador privado o un dispositivo nuevo.
                </span>
              </td>
            </tr>
          </table>

          <!-- Footer -->
          <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top:1px solid #1e2d42;">
            <tr>
              <td style="padding-top:20px;">
                <p style="color:#94a3b8 !important; font-size:12px; font-weight:bold; margin:0 0 4px 0;">
                  Mentes al Mercado · División Software
                </p>
                <p style="color:#64748b !important; font-size:11px; margin:0;">
                  Soporte: servicioalcliente@mentesalmercado.online
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </center>
</body>
</html>"""

    text_content = (
        f"¡Bienvenido a SetterMind AI, {buyer_name}!\n\n"
        f"Ingresa directamente aquí: {magic_link}\n\n"
        f"Tu clave de respaldo: {raw_api_key}\n\n"
        f"Soporte: servicioalcliente@mentesalmercado.online"
    )

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": f"Tu acceso y clave de licencia a SetterMind AI ({buyer_name}) #{timestamp_mark}",
        "html": html_content,
        "text": text_content,
    }

    return resend.Emails.send(params)


def send_password_reset_email(to_email: str, buyer_name: str, reset_token: str) -> object:
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

    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    escaped_name = html.escape(buyer_name or "Setter")
    escaped_link = html.escape(reset_link, quote=True)
    timestamp_mark = str(int(time.time()))[-4:]

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Restablecer Contraseña - SetterMind AI</title>
</head>
<body style="margin:0; padding:20px 0; background-color:#0b111a; font-family:Arial, Helvetica, sans-serif;">
  <center>
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:580px; width:100%; background-color:#111a28; border:1px solid #1e2d42; border-radius:14px; text-align:center;">
      <tr>
        <td style="padding:36px 28px;">
          <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin:0 auto 20px auto; width:52px; height:52px; background-color:#0e2a47; border:2px solid #d4af37; border-radius:12px;">
            <tr>
              <td align="center" valign="middle" style="color:#f3c969; font-size:26px; font-weight:bold; font-family:Arial, sans-serif;">
                M
              </td>
            </tr>
          </table>

          <h1 style="color:#ffffff !important; font-size:22px; font-weight:bold; margin:0 0 16px 0;">
            Restablecer Contraseña
          </h1>

          <p style="color:#cbd5e1 !important; font-size:14px; line-height:22px; margin:0 0 20px 0;">
            Hola <strong style="color:#ffffff !important;">{escaped_name}</strong>, recibimos una solicitud para restablecer la contraseña de tu cuenta en SetterMind AI.
          </p>

          <p style="color:#94a3b8 !important; font-size:13px; line-height:20px; margin:0 0 26px 0;">
            Haz clic en el siguiente botón para definir tu nueva contraseña. Este enlace expira en 1 hora:
          </p>

          <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin:0 auto 26px auto;">
            <tr>
              <td align="center" style="background-color:#0284c7; border-radius:8px;">
                <a href="{escaped_link}" target="_blank" style="display:inline-block; padding:14px 32px; font-family:Arial, sans-serif; font-size:14px; font-weight:bold; color:#ffffff !important; text-decoration:none; border-radius:8px;">
                  Cambiar mi Contraseña
                </a>
              </td>
            </tr>
          </table>

          <p style="color:#64748b !important; font-size:12px; margin:0 0 6px 0; text-align:left;">
            Si el botón no abre automáticamente, copia este enlace:
          </p>
          <p style="margin:0 0 26px 0; text-align:left;">
            <a href="{escaped_link}" target="_blank" style="color:#38bdf8 !important; font-size:12px; word-break:break-all; text-decoration:underline;">
              {escaped_link}
            </a>
          </p>

          <p style="color:#64748b !important; font-size:11px; margin:0 0 20px 0; text-align:left; line-height:16px;">
            Si no solicitaste este cambio, puedes ignorar este mensaje; tu cuenta permanecerá segura.
          </p>

          <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top:1px solid #1e2d42;">
            <tr>
              <td style="padding-top:20px;">
                <p style="color:#94a3b8 !important; font-size:12px; font-weight:bold; margin:0 0 4px 0;">
                  Mentes al Mercado · División Software
                </p>
                <p style="color:#64748b !important; font-size:11px; margin:0;">
                  Soporte: servicioalcliente@mentesalmercado.online
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </center>
</body>
</html>"""

    text_content = (
        f"Hola {buyer_name},\n\n"
        f"Para restablecer tu contraseña en SetterMind AI, visita este enlace:\n"
        f"{reset_link}\n\n"
        f"Este enlace expira en 1 hora.\n\n"
        f"Soporte: servicioalcliente@mentesalmercado.online"
    )

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": f"Restablecer tu contraseña de SetterMind AI #{timestamp_mark}",
        "html": html_content,
        "text": text_content,
    }

    return resend.Emails.send(params)
