"""Adaptadores de API-EXT-04 Envío de correo electrónico."""

import logging
import smtplib
from email.message import EmailMessage

from app.repositories.config.settings import settings

log = logging.getLogger("huella.correo")


class CorreoSMTP:
    """Envía el correo por el servidor SMTP de la empresa."""

    def enviar(self, destinatario: str, asunto: str, contenido: str) -> bool:
        mensaje = EmailMessage()
        mensaje["From"] = settings.correo_remitente
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.set_content(contenido)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as servidor:
                servidor.starttls()
                if settings.smtp_usuario:
                    servidor.login(settings.smtp_usuario, settings.smtp_contrasena)
                servidor.send_message(mensaje)
            return True
        except (smtplib.SMTPException, OSError) as exc:
            log.warning("No fue posible enviar el correo a %s: %s", destinatario, exc)
            return False


class CorreoConsola:
    """Solo para desarrollo: muestra el correo en la consola del servidor en lugar de enviarlo."""

    def enviar(self, destinatario: str, asunto: str, contenido: str) -> bool:
        log.warning("[correo de desarrollo] Para: %s | Asunto: %s\n%s", destinatario, asunto, contenido)
        return True


def obtener_servicio_correo():
    return CorreoSMTP() if settings.smtp_host else CorreoConsola()
