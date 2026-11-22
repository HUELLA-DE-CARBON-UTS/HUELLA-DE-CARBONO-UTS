from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.entities.sesion import EventoBitacora
from app.domain.value_objects.fecha import ahora, en_colombia
from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import (
    BitacoraRepositorioSQLAlchemy, CredencialRepositorioSQLAlchemy, SesionRepositorioSQLAlchemy)
from app.repositories.config.settings import settings
from app.services.contratos.resultado import cuerpo_estandar

FUN = "FUN-07"


def verificar_permiso(db: Session, id_sesion: str, operacion: str) -> dict:
    id_sesion = (id_sesion or "").strip()
    operacion = (operacion or "").strip().upper()
    errores = []
    if not id_sesion:
        errores.append({"field": "sessionId", "detail": "La sesión es obligatoria"})
    if not operacion:
        errores.append({"field": "operation", "detail": "La operación solicitada es obligatoria"})
    if errores:
        return cuerpo_estandar(422, "Los datos de la verificación no son válidos", None, errores, FUN)

    try:
        sesiones = SesionRepositorioSQLAlchemy(db)
        sesion = sesiones.buscar(id_sesion)
        if sesion is None or sesion.estado != "vigente":
            return _sesion_no_valida(id_sesion, f"La sesión {id_sesion} no existe o ya finalizó")

        limite = en_colombia(sesion.ultima_actividad) + timedelta(minutes=settings.access_token_expire_minutes)
        if ahora() > limite:
            sesiones.finalizar(id_sesion)
            db.commit()
            return _sesion_no_valida(id_sesion, f"La sesión {id_sesion} venció por inactividad")

        credencial = CredencialRepositorioSQLAlchemy(db).buscar(sesion.documento)
        rol = RolRepositorioSQLAlchemy(db).buscar_por_id(credencial.id_rol) if credencial else None
        nombre_rol = rol.nombre if rol else "sin rol"

        if sesion.requiere_cambio_contrasena:
            detalle = "Debe cambiar la contraseña temporal antes de continuar"
        elif rol is None or rol.estado != "activo" or operacion not in rol.permisos:
            detalle = f"El rol {nombre_rol} no tiene autorizada la operación {operacion}"
        else:
            detalle = None

        if detalle:
            BitacoraRepositorioSQLAlchemy(db).registrar(EventoBitacora(
                usuario=sesion.documento, tipo_evento="operacion_rechazada", operacion=operacion,
                fecha=ahora(), id_sesion=id_sesion))
            db.commit()
            return cuerpo_estandar(403, "Operación no autorizada", None,
                                   [{"field": "operation", "detail": detalle}], FUN)

        sesiones.registrar_actividad(id_sesion)
        db.commit()
        return cuerpo_estandar(200, "Operación autorizada", {
            "sessionId": id_sesion, "operation": operacion, "role": nombre_rol, "authorized": True,
        }, [], FUN)
    except SQLAlchemyError:
        db.rollback()
        return cuerpo_estandar(503, "No fue posible verificar el permiso de la operación", None,
                               [{"field": "database", "detail": "La base de datos no está disponible"}], FUN)


def _sesion_no_valida(id_sesion: str, detalle: str) -> dict:
    return cuerpo_estandar(401, "Sesión no válida", None, [{"field": "sessionId", "detail": detalle}], FUN)
