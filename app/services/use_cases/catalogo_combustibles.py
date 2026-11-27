from sqlalchemy.orm import Session

from app.domain.entities.catalogo import ElementoCatalogo, Factor
from app.domain.exceptions.errores import Conflicto
from app.repositories.adapters.catalogo_repositorio_sqlalchemy import COMBUSTIBLES, CatalogoRepositorioSQLAlchemy
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion
from app.services.validators import catalogo_validador as v

CAMPO_FACTOR = "emissionFactorKgCO2L"


def _error_fuente(fuente: str) -> dict | None:
    return v.error_texto("source", fuente, "La fuente oficial es obligatoria", 200)


class RegistrarCombustible:

    MENSAJE_503 = "No fue posible registrar el tipo de combustible"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = CatalogoRepositorioSQLAlchemy(db, COMBUSTIBLES)

    def ejecutar(self, nombre, descripcion, factor, fecha_inicio, fuente, responsable: str) -> dict:
        nombre, descripcion, fuente = v.limpiar(nombre), v.limpiar(descripcion), v.limpiar(fuente)
        valor, desde = v.numero(factor), v.fecha(fecha_inicio)
        v.lanzar([
            v.error_texto("name", nombre, "El nombre del combustible es obligatorio", 60),
            v.error_texto("description", descripcion, "La descripción es obligatoria", 200),
            None if valor is not None and valor > 0 else
            {"field": CAMPO_FACTOR, "detail": "Debe ser numérico y mayor que 0"},
            v.error_fecha("startDate", desde),
            _error_fuente(fuente),
        ], "Los datos del combustible no son válidos", CAMPO_FACTOR, "El factor de emisión no es válido")

        duplicado = Conflicto("El combustible ya está registrado", [
            {"field": "name", "detail": f"Ya existe el combustible {nombre}"}])
        with transaccion(self.db, self.MENSAJE_503, duplicado):
            existente = self.repositorio.buscar_por_nombre(nombre)
            if existente is not None:
                raise Conflicto("El combustible ya está registrado", [
                    {"field": "name", "detail": f"Ya existe el combustible {existente.nombre}"}])
            combustible = ElementoCatalogo(id=self.repositorio.siguiente_id(), nombre=nombre, descripcion=descripcion)
            self.repositorio.guardar(combustible, Factor(valor=valor, vigente_desde=desde, responsable=responsable,
                                                         fuente=fuente))
            self.db.commit()

        return {"fuelId": combustible.id, "name": combustible.nombre, "status": api.estado(combustible.estado),
                "emissionFactorKgCO2L": valor, "validFrom": desde.isoformat(), "source": fuente}
