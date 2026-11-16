"""Contrato del repositorio de usuarios."""

from typing import Protocol

from app.domain.entities.usuario import Usuario


class UsuarioRepositorio(Protocol):
    def buscar_por_documento(self, documento: str) -> Usuario | None: ...

    def buscar_por_correo(self, correo: str) -> Usuario | None: ...

    def siguiente_id(self) -> str: ...

    def agregar(self, usuario: Usuario, responsable: str) -> None: ...
