"""Identificación de la sesión que hace la solicitud.

Mientras no exista el inicio de sesión (HU-06), la única sesión válida es la
del administrador inicial, que se envía como `Authorization: Bearer <TOKEN_ADMIN_INICIAL>`.
"""

import secrets

from fastapi import Header

from app.domain.exceptions.errores import SesionNoValida
from app.repositories.config.settings import settings
from app.services.use_cases.verificar_permiso import SesionUsuario


def obtener_sesion(authorization: str | None = Header(default=None)) -> SesionUsuario:
    token = (authorization or "").removeprefix("Bearer ").strip()
    esperado = settings.token_admin_inicial
    if not token or not esperado or not secrets.compare_digest(token, esperado):
        raise SesionNoValida("No hay una sesión vigente", [
            {"campo": "sesion", "detalle": "Debe iniciar sesión para realizar esta operación"},
        ])
    return SesionUsuario(documento=settings.documento_admin_inicial, rol="Administrador")
