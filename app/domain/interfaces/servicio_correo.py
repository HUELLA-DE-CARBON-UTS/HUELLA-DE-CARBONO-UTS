from typing import Protocol


class ServicioCorreo(Protocol):
    def enviar(self, destinatario: str, asunto: str, contenido: str) -> bool:
        ...
