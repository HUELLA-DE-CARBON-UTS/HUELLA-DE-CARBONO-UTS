from datetime import date

from app.domain.entities.catalogo import Factor
from app.domain.value_objects.fecha import ahora


def hoy() -> date:
    return ahora().date()


def factor_del_dia(factores: list[Factor], dia: date) -> Factor | None:
    return next((f for f in factores if f.aplica_en(dia)), None)


def plural_estado(estado: str) -> str:
    return "activos" if estado == "activo" else "inactivos"
