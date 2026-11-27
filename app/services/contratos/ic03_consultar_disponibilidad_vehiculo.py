from sqlalchemy.orm import Session

from app.repositories.adapters.recorrido_repositorio_sqlalchemy import RecorridoRepositorioSQLAlchemy
from app.repositories.adapters.vehiculo_repositorio_sqlalchemy import VehiculoRepositorioSQLAlchemy
from app.services.use_cases.catalogo_comun import hoy


def consultar_disponibilidad_vehiculo(db: Session, placa: str) -> dict:
    repositorio = VehiculoRepositorioSQLAlchemy(db)
    vehiculo = repositorio.buscar(placa)
    if vehiculo is None:
        return {"existe": False}
    fichas = repositorio.fichas(placa)
    dia = hoy()
    ficha = next((f for f in fichas if f.aplica_en(dia)), fichas[-1] if fichas else None)
    return {"existe": True, "placa": vehiculo.placa, "estado": vehiculo.estado, "idSede": vehiculo.id_sede,
            "idTipo": ficha.id_tipo, "idCombustible": ficha.id_combustible,
            "recorridoAbierto": RecorridoRepositorioSQLAlchemy(db).abierto_de(placa)}


def detalle_no_disponible(info: dict) -> str:
    if info["estado"] == "asignado" and info.get("recorridoAbierto"):
        return f"El vehículo {info['placa']} está asignado al recorrido {info['recorridoAbierto']}"
    if info["estado"] == "asignado":
        return f"El vehículo {info['placa']} está asignado a un recorrido abierto"
    return f"El vehículo {info['placa']} está fuera de servicio"
