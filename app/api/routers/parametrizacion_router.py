from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import SesionUsuario
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.parametrizacion import SedeEntrada
from app.api.schemas.respuesta import RespuestaEstandar, ejemplo, responder, ruta
from app.api.dependencies.db import get_db
from app.api.dependencies.roles import requiere_permiso
from app.api.schemas.parametrizacion import SedeEntrada
from app.api.schemas.respuesta import RespuestaEstandar, responder
from app.repositories.adapters.sede_repositorio_sqlalchemy import SedeRepositorioSQLAlchemy
from app.services.use_cases.registrar_sede import RegistrarSede

router = APIRouter(prefix="/api/v1", tags=["MOD-03 Parametrización"])

SIN_SESION = {401: {"description": "No hay una sesión vigente"}}
_ejemplo_exito = {
    "estado": "exito", "codigo": 201, "mensaje": "Sede registrada correctamente",
    "datos": {"idSede": "SED-05", "nombre": "Barranquilla", "ciudad": "Barranquilla",
              "direccion": "Calle 30 # 1-25, zona industrial", "responsable": "Carolina Herrera Pérez",
              "estado": "activa"},
    "errores": [],
    "metadatos": {"funcionalidad": "FUN-16", "fecha": "2026-11-03T09:15:00-05:00"},
}

_ejemplo_conflicto = {
    "estado": "error", "codigo": 409, "mensaje": "Ya existe una sede con ese nombre en la ciudad", "datos": None,
    "errores": [{"campo": "nombre", "detalle": "La sede Barranquilla ya está registrada en Barranquilla"}],
    "metadatos": {"funcionalidad": "FUN-16", "fecha": "2026-11-03T09:16:00-05:00"},
}


@router.post(
    "/sedes",
    summary="HU-16 Registrar una nueva sede",
    description="Registra una sede con su nombre, ciudad, dirección y responsable. La sede queda en estado "
                "«activa» con su fecha de creación. No se permiten dos sedes con el mismo nombre en la misma "
                "ciudad. Requiere el permiso FUN-16 (IC-01).",
    response_model=RespuestaEstandar, status_code=201,
    openapi_extra=ruta("FUN-16", "No fue posible registrar la sede"),
    responses={
        201: ejemplo(201, "Sede registrada correctamente", {
            "idSede": "SED-05", "nombre": "Barranquilla", "ciudad": "Barranquilla",
            "direccion": "Calle 30 # 1-25, zona industrial", "responsable": "Carolina Herrera Pérez",
            "estado": "activa"}, None, "FUN-16"),
        **SIN_SESION,
        403: {"description": "El rol de la sesión no tiene el permiso FUN-16"},
        409: ejemplo(409, "Ya existe una sede con ese nombre en la ciudad", None,
                     [{"campo": "nombre", "detalle": "La sede Barranquilla ya está registrada en Barranquilla"}], "FUN-16"),
    description=(
        "Registra una sede con su nombre, ciudad, dirección y responsable. La sede queda en estado "
        "«activa» con su fecha de creación. No se permiten dos sedes con el mismo nombre en la misma "
        "ciudad. Requiere una sesión vigente con el permiso FUN-16 (IC-01)."
    ),
    response_model=RespuestaEstandar,
    status_code=201,
    responses={
        201: {"description": "Sede registrada",
              "content": {"application/json": {"example": _ejemplo_exito}}},
        401: {"description": "No hay una sesión vigente"},
        403: {"description": "El rol de la sesión no tiene el permiso FUN-16"},
        409: {"description": "Ya existe una sede con ese nombre en la ciudad",
              "content": {"application/json": {"example": _ejemplo_conflicto}}},
        422: {"description": "Falta un campo obligatorio o supera su longitud"},
        503: {"description": "No fue posible registrar la sede"},
    },
)
def registrar_sede(
    entrada: SedeEntrada | None = Body(None),
    _sesion: SesionUsuario = Depends(requiere_permiso("FUN-16", "No tiene permiso para registrar sedes")),
    db: Session = Depends(get_db),
):
    entrada = entrada or SedeEntrada()
    entrada: SedeEntrada = Body(...),
    _sesion=Depends(requiere_permiso("FUN-16", "No tiene permiso para registrar sedes")),
    db: Session = Depends(get_db),
):
    sede = RegistrarSede(SedeRepositorioSQLAlchemy(db)).ejecutar(
        entrada.nombre, entrada.ciudad, entrada.direccion, entrada.responsable)
    datos = {
        "idSede": sede.id_sede, "nombre": sede.nombre, "ciudad": sede.ciudad,
        "direccion": sede.direccion, "responsable": sede.responsable, "estado": sede.estado,
    }
    return responder(201, "Sede registrada correctamente", datos, funcionalidad="FUN-16")
