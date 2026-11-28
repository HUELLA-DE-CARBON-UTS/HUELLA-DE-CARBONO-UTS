from datetime import date

from sqlalchemy.orm import Session

from app.domain.entities.recorrido import Recorrido
from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.services.contratos.ic16_consultar_vehiculos_por_criterio import placas_de_sede
from app.services.validators.recorrido_validador import en_rango


def consultar_datos_recorridos(db: Session, inicio: date | None = None, fin: date | None = None,
                               placa: str | None = None, sede: str | None = None) -> list[Recorrido]:
    placas = placas_de_sede(db, sede) if sede else None
    return [r for r in RecorridoRepositorioSQLAlchemy(db).listar()
            if r.estado == "cerrado" and en_rango(r.fecha_cierre, inicio, fin)
            and (not placa or r.placa == placa) and (placas is None or r.placa in placas)]
