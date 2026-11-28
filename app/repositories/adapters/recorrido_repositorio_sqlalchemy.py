from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.recorrido import Recorrido, ResultadoRecorrido
from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos_recorridos import RecorridoModelo, ResultadoRecorridoModelo

CAMPOS_RECORRIDO = ("codigo", "placa", "origen", "destino", "fecha_programada", "id_tipo", "id_combustible",
                    "distancia_estimada_km", "estado", "fecha_cierre", "distancia_km", "consumo_registrado_l",
                    "motivo_cancelacion")
CAMPOS_RESULTADO = ("codigo", "distancia_km", "consumo_registrado_l", "estado_consumo", "causa_consumo",
                    "id_factor_consumo", "factor_consumo_lkm", "consumo_estimado_l", "rendimiento_lkm",
                    "desviacion_pct", "estado_emisiones", "causa_emisiones", "id_factor_emision",
                    "factor_emision_kgco2l", "fuente_emision", "emisiones_kgco2", "version")


def _recorrido(modelo: RecorridoModelo) -> Recorrido:
    return Recorrido(**{campo: getattr(modelo, campo) for campo in CAMPOS_RECORRIDO})


def _resultado(modelo: ResultadoRecorridoModelo) -> ResultadoRecorrido:
    return ResultadoRecorrido(**{campo: getattr(modelo, campo) for campo in CAMPOS_RESULTADO})


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

    def actualizar(self, recorrido: Recorrido) -> None:
        modelo = self.sesion.get(RecorridoModelo, recorrido.codigo)
        for campo in CAMPOS_RECORRIDO:
            setattr(modelo, campo, getattr(recorrido, campo))
        self.sesion.flush()

    def abierto_de(self, placa: str) -> str | None:
        return self.sesion.scalar(select(RecorridoModelo.codigo).where(
            RecorridoModelo.placa == placa, RecorridoModelo.estado == "programado"))

    def guardar_resultado(self, resultado: ResultadoRecorrido) -> None:
        anteriores = self.sesion.scalars(select(ResultadoRecorridoModelo).where(
            ResultadoRecorridoModelo.codigo == resultado.codigo, ResultadoRecorridoModelo.vigente.is_(True)))
        for anterior in anteriores:
            anterior.vigente = False
        datos = {campo: getattr(resultado, campo) for campo in CAMPOS_RESULTADO}
        self.sesion.add(ResultadoRecorridoModelo(**datos, vigente=True, fecha_calculo=ahora()))
        self.sesion.flush()

    def resultado_vigente(self, codigo: str) -> ResultadoRecorrido | None:
        modelo = self.sesion.scalar(select(ResultadoRecorridoModelo).where(
            ResultadoRecorridoModelo.codigo == codigo, ResultadoRecorridoModelo.vigente.is_(True)))
        return _resultado(modelo) if modelo else None
