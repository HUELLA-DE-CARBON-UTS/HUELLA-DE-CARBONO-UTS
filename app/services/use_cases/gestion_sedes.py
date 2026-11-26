import unicodedata

from app.domain.exceptions.errores import DatosNoValidos, NoEncontrado
from app.repositories.adapters.sede_repositorio_sqlalchemy import SedeRepositorioSQLAlchemy
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion
from app.services.validators import sede_validador

ESTADOS_SEDE = ("active", "inactive")


def _orden(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


class ConsultarSedes:

    MENSAJE_503 = "No fue posible consultar las sedes"

    def __init__(self, db):
        self.db = db

    def ejecutar(self, ciudad: str | None = None, estado: str | None = None) -> list[dict]:
        ciudad = sede_validador.limpiar(ciudad) or None
        estado = sede_validador.limpiar(estado).lower() or None
        if estado and estado not in ESTADOS_SEDE:
            raise DatosNoValidos("Los criterios de consulta no son válidos", [
                {"field": "status", "detail": 'El estado debe ser "active" o "inactive"'}])
        estado = api.estado_interno(estado, femenino=True) if estado else None

        with transaccion(self.db, self.MENSAJE_503):
            sedes = SedeRepositorioSQLAlchemy(self.db).listar(ciudad, estado)
        if not sedes:
            if ciudad:
                detalle = f"No hay sedes registradas en {ciudad}" + (f" en estado {estado}" if estado else "")
                raise NoEncontrado("Sin resultados", [{"field": "city", "detail": detalle}])
            detalle = f"No hay sedes en estado {estado}" if estado else "No hay sedes registradas"
            raise NoEncontrado("Sin resultados", [{"field": "status", "detail": detalle}])
        sedes = sorted(sedes, key=lambda s: (_orden(s.ciudad), _orden(s.nombre)))
        return [{"siteId": s.id_sede, "name": s.nombre, "city": s.ciudad, "manager": s.responsable,
                 "status": api.estado(s.estado)} for s in sedes]
