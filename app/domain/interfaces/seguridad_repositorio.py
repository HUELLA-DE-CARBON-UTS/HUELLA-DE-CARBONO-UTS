"""Contratos de los repositorios de MOD-02 Gestión de Seguridad."""

from typing import Protocol


class CredencialRepositorio(Protocol):

    def crear(self, documento: str, hash_contrasena: str, temporal: bool, id_rol: str) -> None: ...
