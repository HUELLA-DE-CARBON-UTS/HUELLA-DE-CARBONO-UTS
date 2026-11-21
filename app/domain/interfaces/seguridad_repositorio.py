from typing import Protocol

from app.domain.entities.sesion import Credencial, EventoBitacora, Sesion


class CredencialRepositorio(Protocol):
    def buscar(self, documento: str) -> Credencial | None: ...

    def crear(self, documento: str, hash_contrasena: str, temporal: bool, id_rol: str) -> None: ...

    def marcar_usada(self, documento: str) -> None: ...


class SesionRepositorio(Protocol):
    def crear(self, documento: str, requiere_cambio: bool) -> tuple[Sesion, str]: ...

    def buscar_por_token(self, token: str) -> Sesion | None: ...


class BitacoraRepositorio(Protocol):
    def registrar(self, evento: EventoBitacora) -> None: ...
