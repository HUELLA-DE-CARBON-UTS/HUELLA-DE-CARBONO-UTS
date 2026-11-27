from sqlalchemy.orm import Session

from app.repositories.adapters.vehiculo_repositorio_sqlalchemy import VehiculoRepositorioSQLAlchemy

ESTADOS_OPERATIVOS = ("asignado", "disponible")


def cambiar_estado_operativo_vehiculo(db: Session, placa: str, estado: str) -> bool:
    if estado not in ESTADOS_OPERATIVOS:
        return False
    repositorio = VehiculoRepositorioSQLAlchemy(db)
    vehiculo = repositorio.buscar(placa)
    if vehiculo is None:
        return False
    vehiculo.estado = estado
    repositorio.actualizar(vehiculo)
    return True
