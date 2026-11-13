"""Contrato del repositorio de roles."""

from typing import Protocol

from app.domain.entities.rol import Rol


class RolRepositorio(Protocol):
    def buscar_por_nombre(self, nombre: str) -> Rol | None: ...

    def operaciones_existentes(self, codigos: list[str]) -> set[str]: ...

    def siguiente_id(self) -> str: ...

    def guardar(self, rol: Rol, responsable: str) -> Rol: ...
