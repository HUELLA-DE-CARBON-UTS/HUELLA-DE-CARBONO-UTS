from sqlalchemy.orm import Session

from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos import HistorialCambioModelo


class HistorialRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def registrar(self, entidad: str, id_entidad: str, tipo_cambio: str, anterior: str, nuevo: str,
                  responsable: str, motivo: str = "") -> None:
        self.sesion.add(HistorialCambioModelo(entidad=entidad, id_entidad=id_entidad, tipo_cambio=tipo_cambio,
                                              valor_anterior=anterior, valor_nuevo=nuevo, motivo=motivo,
                                              fecha=ahora(), responsable=responsable))
        self.sesion.flush()
