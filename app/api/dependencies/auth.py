import secrets

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.exceptions.errores import SesionNoValida
from app.repositories.config.settings import settings
from app.services.use_cases.verificar_permiso import SesionUsuario

security = HTTPBearer(auto_error=False)


def obtener_sesion(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> SesionUsuario:
    token = (credentials.credentials if credentials else "").strip()
    esperado = settings.token_admin_inicial
    if not token or not esperado or not secrets.compare_digest(token, esperado):
        raise SesionNoValida("No hay una sesión vigente", [
            {"campo": "sesion", "detalle": "Debe iniciar sesión para realizar esta operación"},
        ])
    return SesionUsuario(documento=settings.documento_admin_inicial, rol="Administrador")
    return SesionUsuario(documento=settings.documento_admin_inicial, rol="Administrador")
