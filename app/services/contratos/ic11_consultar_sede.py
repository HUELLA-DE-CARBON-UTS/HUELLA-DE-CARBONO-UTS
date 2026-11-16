"""IC-11 consultarSede: verifica que una sede exista y esté activa y obtiene su
nombre, sin que MOD-01 lea las tablas de MOD-03."""

import re

from sqlalchemy.orm import Session

from app.repositories.adapters.sede_repositorio_sqlalchemy import SedeRepositorioSQLAlchemy

FORMATO_ID_SEDE = re.compile(r"^SED-\d+$", re.IGNORECASE)


def consultar_sede(db: Session, referencia: str) -> dict:
    """Recibe el identificador (SED-01) o el nombre de la sede.

    Retorna {"existe": False} si no la encuentra, o {"existe": True, "idSede", "nombre",
    "ciudad", "estado"}. Si el nombre corresponde a varias sedes, agrega "ambigua": True.
    """
    repo = SedeRepositorioSQLAlchemy(db)
    referencia = " ".join((referencia or "").split())
    if FORMATO_ID_SEDE.match(referencia):
        sedes = [s for s in [repo.buscar_por_id(referencia.upper())] if s]
    else:
        sedes = repo.buscar_por_nombre(referencia)
    if not sedes:
        return {"existe": False}
    if len(sedes) > 1:
        activas = [s for s in sedes if s.estado == "activa"]
        if len(activas) == 1:
            sedes = activas
        else:
            return {"existe": True, "ambigua": True, "nombre": referencia}
    sede = sedes[0]
    return {"existe": True, "idSede": sede.id_sede, "nombre": sede.nombre, "ciudad": sede.ciudad,
            "estado": sede.estado}


def error_de_sede(info: dict, referencia: str, campo: str) -> dict | None:
    """Detalle del error cuando la sede no sirve para asignarla a un usuario."""
    if not info["existe"]:
        return {"campo": campo, "detalle": f"La sede {referencia} no existe"}
    if info.get("ambigua"):
        return {"campo": campo, "detalle": f"Hay varias sedes llamadas {referencia}; indique su identificador (SED-XX)"}
    if info["estado"] != "activa":
        return {"campo": campo, "detalle": f"La sede {info['nombre']} se encuentra inactiva"}
    return None
