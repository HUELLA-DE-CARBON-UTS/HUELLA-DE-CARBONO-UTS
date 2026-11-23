from sqlalchemy.orm import Session

from app.domain.entities.sesion import EventoBitacora
from app.domain.value_objects.fecha import ahora
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import (
    BitacoraRepositorioSQLAlchemy, SesionRepositorioSQLAlchemy)


def cerrar_sesiones_usuario(db: Session, documento: str, operacion: str) -> int:
    sesiones = SesionRepositorioSQLAlchemy(db)
    bitacora = BitacoraRepositorioSQLAlchemy(db)
    abiertas = sesiones.vigentes_de(documento)
    for sesion in abiertas:
        sesiones.finalizar(sesion.id_sesion)
        bitacora.registrar(EventoBitacora(usuario=documento, tipo_evento="salida", operacion=operacion,
                                          fecha=ahora(), id_sesion=sesion.id_sesion))
    return len(abiertas)
