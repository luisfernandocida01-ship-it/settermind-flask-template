import html
import os
from urllib.parse import urlencode

import resend


def send_welcome_email(to_email: str, buyer_name: str, raw_api_key: str) -> object:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY no está configurada.")

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
    escaped_name = html.escape(buyer_name)
    escaped_key = html.escape(raw_api_key)
    escaped_link = html.escape(magic_link, quote=True)

    html_content = f"""<!doctype html>
<html lang="es">
  <body style="margin:0;padding:30px 10px;background:#0B111A;font-family:Arial,sans-serif;color:#CBD5E1">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:580px;margin:auto;background:#111A28;border:1px solid #1E2D42;border-radius:14px">
      <tr><td style="padding:35px 25px;text-align:center">
        <div style="margin:0 auto 20px;width:55px;height:55px;line-height:55px;background:#0E2A47;border:2px solid #D4AF37;border-radius:12px;color:#F3C969;font-size:26px;font-weight:bold">M</div>
        <h1 style="color:#fff;font-size:24px">¡Bienvenido a SetterMind AI!</h1>
        <p>Hola <strong style="color:#fff">{escaped_name}</strong>, tu cuenta ha sido aprovisionada con éxito.</p>
        <p>Utiliza este enlace para ingresar:</p>
        <p style="margin:25px">
          <a href="{escaped_link}" style="display:inline-block;padding:14px 28px;border-radius:8px;background:#0284C7;color:#fff;text-decoration:none;font-weight:bold">Ingresar a SetterMind AI</a>
        </p>
        <p style="font-size:12px;color:#64748B">Si el botón no funciona, copia este enlace:</p>
        <p><a href="{escaped_link}" style="color:#38BDF8;word-break:break-all">{escaped_link}</a></p>
        <div style="padding:15px;background:#06090E;border:1px dashed #1E2D42;border-radius:8px;text-align:left">
          <p style="color:#94A3B8;font-size:11px;font-weight:bold">CLAVE API DE RESPALDO</p>
          <code style="color:#38BDF8;word-break:break-all">{escaped_key}</code>
          <p style="color:#64748B;font-size:11px">Guarda esta clave para usarla en otro dispositivo.</p>
        </div>
        <p style="padding-top:18px;border-top:1px solid #1E2D42;color:#64748B;font-size:12px">
          Mentes al Mercado · Soporte: servicioalcliente@mentesalmercado.online
        </p>
      </td></tr>
    </table>
  </body>
</html>"""
    text_content = (
        f"¡Bienvenido a SetterMind AI, {buyer_name}!\n\n"
        f"Ingresa aquí: {magic_link}\n\n"
        f"Tu clave API de respaldo: {raw_api_key}\n"
    )

    resend.api_key = api_key
    return resend.Emails.send(
        {
            "from": sender_email,
            "to": [to_email],
            "subject": "Tu acceso y clave de licencia a SetterMind AI",
            "html": html_content,
            "text": text_content,
        }
    )
