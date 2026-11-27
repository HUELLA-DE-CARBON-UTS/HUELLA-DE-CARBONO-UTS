from datetime import date

from sqlalchemy.orm import Session

from app.repositories.adapters.catalogo_repositorio_sqlalchemy import (
    COMBUSTIBLES, TIPOS_VEHICULO, CatalogoRepositorioSQLAlchemy)
from app.services.use_cases.catalogo_comun import factor_del_dia, hoy
from app.services.validators.catalogo_validador import FORMATO_ID

CATALOGOS = {"tipo": (TIPOS_VEHICULO, "TV"), "combustible": (COMBUSTIBLES, "CB")}


def consultar_catalogo_vigente(db: Session, catalogo: str, referencia: str, dia: date | None = None) -> dict:
    configuracion, prefijo = CATALOGOS[catalogo]
    repositorio = CatalogoRepositorioSQLAlchemy(db, configuracion)
    referencia = " ".join((referencia or "").split())
    if FORMATO_ID[prefijo].match(referencia.upper()):
        elemento = repositorio.buscar(referencia.upper())
    else:
        elemento = repositorio.buscar_por_nombre(referencia) if referencia else None
    if elemento is None:
        return {"existe": False}
    factor = factor_del_dia(repositorio.factores(elemento.id), dia or hoy())
    return {"existe": True, "id": elemento.id, "nombre": elemento.nombre, "estado": elemento.estado,
            "factor": factor.valor if factor else None}


def error_de_catalogo(info: dict, catalogo: str, referencia: str, campo: str) -> dict | None:
    etiqueta = "el tipo de vehículo" if catalogo == "tipo" else "el combustible"
    if not info["existe"]:
        return {"campo": campo, "detalle": f"No existe {etiqueta} {referencia}"}
    if info["estado"] != "activo":
        return {"campo": campo, "detalle": f"{etiqueta.capitalize()} {info['nombre']} se encuentra inactivo"}
    if info["factor"] is None:
        if catalogo == "tipo":
            return {"campo": campo, "detalle": f"El tipo {info['nombre']} no tiene factor de consumo vigente"}
        return {"campo": campo, "detalle": f"El combustible {info['nombre']} no tiene factor de emisión vigente"}
    return None


def solo_falta_factor(errores: list[dict]) -> bool:
    return all("factor" in e["detalle"] for e in errores)
