from datetime import date

from sqlalchemy.orm import Session

from app.repositories.adapters.catalogo_repositorio_sqlalchemy import TIPOS_VEHICULO, CatalogoRepositorioSQLAlchemy
from app.services.use_cases.catalogo_comun import factor_del_dia


def obtener_factor_consumo_vigente(db: Session, id_tipo: str, dia: date) -> dict | None:
    factor = factor_del_dia(CatalogoRepositorioSQLAlchemy(db, TIPOS_VEHICULO).factores(id_tipo), dia)
    if factor is None:
        return None
    return {"idFactor": f"FC-{factor.id:04d}", "factorConsumoLkm": factor.valor}
