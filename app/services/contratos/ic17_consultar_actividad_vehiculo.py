from sqlalchemy.orm import Session

from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy


def consultar_actividad_vehiculo(db: Session, placa: str) -> dict:
    cerrados = [r for r in RecorridoRepositorioSQLAlchemy(db).listar() if r.placa == placa and r.estado == "cerrado"]
    ultimo = max((r.fecha_cierre for r in cerrados if r.fecha_cierre), default=None)
    return {"totalRecorridos": len(cerrados), "ultimoRecorridoCerrado": ultimo.isoformat() if ultimo else None}
