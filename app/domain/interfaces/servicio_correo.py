from typing import Protocol


class ServicioCorreo(Protocol):
    def enviar(self, destinatario: str, asunto: str, contenido: str) -> bool:
        """Retorna True si el correo se envió y False si el servicio no respondió."""
        ...
