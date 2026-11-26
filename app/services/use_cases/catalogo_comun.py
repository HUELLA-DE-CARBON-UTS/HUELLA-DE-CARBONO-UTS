from datetime import date, timedelta

from app.domain.entities.catalogo import Factor
from app.domain.exceptions.errores import DatosNoValidos
from app.domain.interfaces.catalogo_repositorio import CatalogoRepositorio
from app.domain.value_objects.fecha import ahora


def hoy() -> date:
    return ahora().date()


def reemplazar_factor(repositorio: CatalogoRepositorio, identificador: str, nuevo: Factor) -> Factor | None:
    anterior = repositorio.factor_abierto(identificador)
    if anterior is not None:
        inicio = anterior.vigente_desde.isoformat()
        if nuevo.vigente_desde < anterior.vigente_desde:
            raise DatosNoValidos("La fecha del nuevo factor no es válida", [
                {"field": "startDate", "detail": f"No puede ser anterior al inicio del factor vigente ({inicio})"}])
        if nuevo.vigente_desde == anterior.vigente_desde:
            raise DatosNoValidos("La fecha del nuevo factor no es válida", [
                {"field": "startDate", "detail": f"Debe ser posterior al inicio del factor vigente ({inicio})"}])
        anterior.vigente_hasta = nuevo.vigente_desde - timedelta(days=1)
        repositorio.cerrar_factor(anterior, anterior.vigente_hasta)
    repositorio.agregar_factor(identificador, nuevo)
    return anterior


def factor_del_dia(factores: list[Factor], dia: date) -> Factor | None:
    return next((f for f in factores if f.aplica_en(dia)), None)


def plural_estado(estado: str) -> str:
    return "activos" if estado == "activo" else "inactivos"
