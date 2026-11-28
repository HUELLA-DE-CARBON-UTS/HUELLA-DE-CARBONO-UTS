from datetime import date

from sqlalchemy.orm import Session

from app.repositories.adapters.catalogo_repositorio_sqlalchemy import COMBUSTIBLES, CatalogoRepositorioSQLAlchemy
from app.services.use_cases.catalogo_comun import factor_del_dia


def obtener_factor_emision_vigente(db: Session, id_combustible: str, dia: date) -> dict | None:
    factor = factor_del_dia(CatalogoRepositorioSQLAlchemy(db, COMBUSTIBLES).factores(id_combustible), dia)
    if factor is None:
        return None
    return {"idFactor": f"FE-{factor.id:04d}", "factorEmisionKgCO2L": factor.valor, "fuente": factor.fuente}
