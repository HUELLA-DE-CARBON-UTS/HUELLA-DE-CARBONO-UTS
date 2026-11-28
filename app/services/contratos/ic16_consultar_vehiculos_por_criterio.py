from sqlalchemy.orm import Session

from app.repositories.adapters.vehiculo_repositorio_sqlalchemy import VehiculoRepositorioSQLAlchemy
from app.services.contratos.ic11_consultar_sede import ids_de_sede


def placas_de_sede(db: Session, sede: str) -> set[str]:
    sedes = set(ids_de_sede(db, sede))
    return {v.placa for v in VehiculoRepositorioSQLAlchemy(db).listar() if v.id_sede in sedes}
