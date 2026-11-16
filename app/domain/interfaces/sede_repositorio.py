from typing import Protocol

from app.domain.entities.sede import Sede


class SedeRepositorio(Protocol):
    def existe_en_ciudad(self, nombre: str, ciudad: str) -> bool: ...

    def siguiente_id(self) -> str: ...

    def guardar(self, sede: Sede) -> Sede: ...
