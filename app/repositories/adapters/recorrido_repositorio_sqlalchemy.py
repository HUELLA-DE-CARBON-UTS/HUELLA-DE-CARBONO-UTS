from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.recorrido import Recorrido
from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos_recorridos import RecorridoModelo

CAMPOS_RECORRIDO = ("codigo", "placa", "origen", "destino", "fecha_programada", "id_tipo", "id_combustible",
                    "distancia_estimada_km", "estado", "fecha_cierre", "distancia_km", "consumo_registrado_l",
                    "motivo_cancelacion")


def _recorrido(modelo: RecorridoModelo) -> Recorrido:
    return Recorrido(**{campo: getattr(modelo, campo) for campo in CAMPOS_RECORRIDO})


class RecorridoRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def siguiente_codigo(self) -> str:
        codigos = self.sesion.scalars(select(RecorridoModelo.codigo)).all()
        mayor = max((int(c.split("-")[1]) for c in codigos), default=0)
        return f"REC-{mayor + 1:04d}"

    def guardar(self, recorrido: Recorrido, responsable: str) -> None:
        datos = {campo: getattr(recorrido, campo) for campo in CAMPOS_RECORRIDO}
        self.sesion.add(RecorridoModelo(**datos, fecha_creacion=ahora(), responsable=responsable))
        self.sesion.flush()

    def buscar(self, codigo: str) -> Recorrido | None:
        modelo = self.sesion.get(RecorridoModelo, codigo)
        return _recorrido(modelo) if modelo else None

    def abierto_de(self, placa: str) -> str | None:
        return self.sesion.scalar(select(RecorridoModelo.codigo).where(
            RecorridoModelo.placa == placa, RecorridoModelo.estado == "programado"))
