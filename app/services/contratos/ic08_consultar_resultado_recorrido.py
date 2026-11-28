from sqlalchemy.orm import Session

from app.domain.entities.recorrido import ResultadoRecorrido
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy


def consultar_resultado_recorrido(db: Session, codigo: str) -> ResultadoRecorrido | None:
    return RecorridoRepositorioSQLAlchemy(db).resultado_vigente(codigo)
