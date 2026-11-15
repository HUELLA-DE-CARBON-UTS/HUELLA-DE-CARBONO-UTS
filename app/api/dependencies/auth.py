import secrets

from fastapi import Header

from app.domain.exceptions.errores import SesionNoValida
from app.repositories.config.settings import settings
from app.services.use_cases.verificar_permiso import SesionUsuario


def obtener_sesion(
    authorization: str | None = Header(default=None, include_in_schema=False),
    x_authorization: str | None = Header(default=None, alias="X-Authorization"),
) -> SesionUsuario:
    raw = x_authorization or authorization or ""
    token = raw.removeprefix("Bearer ").strip()
    esperado = settings.token_admin_inicial
    if not token or not esperado or not secrets.compare_digest(token, esperado):
        raise SesionNoValida("No hay una sesión vigente", [
            {"campo": "sesion", "detalle": "Debe iniciar sesión para realizar esta operación"},
        ])
    return SesionUsuario(documento=settings.documento_admin_inicial, rol="Administrador")