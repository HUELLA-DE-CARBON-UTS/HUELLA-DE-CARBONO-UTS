from sqlalchemy.orm import Session

from app.domain.entities.catalogo import ElementoCatalogo, Factor
from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.catalogo_repositorio_sqlalchemy import COMBUSTIBLES, CatalogoRepositorioSQLAlchemy
from app.services.mappers import api
from app.services.use_cases.catalogo_comun import factor_del_dia, hoy, plural_estado
from app.services.use_cases.transaccion import transaccion
from app.services.validators import catalogo_validador as v

CAMPO_FACTOR = "factorEmisionKgCO2L"


def _error_fuente(fuente: str) -> dict | None:
    return v.error_texto("fuente", fuente, "La fuente oficial es obligatoria", 200)


class RegistrarCombustible:

    MENSAJE_503 = "No fue posible registrar el tipo de combustible"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = CatalogoRepositorioSQLAlchemy(db, COMBUSTIBLES)

    def ejecutar(self, nombre, descripcion, factor, fecha_inicio, fuente, responsable: str) -> dict:
        nombre, descripcion, fuente = v.limpiar(nombre), v.limpiar(descripcion), v.limpiar(fuente)
        valor, desde = v.numero(factor), v.fecha(fecha_inicio)
        v.lanzar([
            v.error_texto("nombre", nombre, "El nombre del combustible es obligatorio", 60),
            v.error_texto("descripcion", descripcion, "La descripción es obligatoria", 200),
            None if valor is not None and valor > 0 else
            {"campo": CAMPO_FACTOR, "detalle": "Debe ser numérico y mayor que 0"},
            v.error_fecha("fechaInicio", desde),
            _error_fuente(fuente),
        ], "Los datos del combustible no son válidos", CAMPO_FACTOR, "El factor de emisión no es válido")

        duplicado = Conflicto("El combustible ya está registrado", [
            {"campo": "nombre", "detalle": f"Ya existe el combustible {nombre}"}])
        with transaccion(self.db, self.MENSAJE_503, duplicado):
            existente = self.repositorio.buscar_por_nombre(nombre)
            if existente is not None:
                raise Conflicto("El combustible ya está registrado", [
                    {"campo": "nombre", "detalle": f"Ya existe el combustible {existente.nombre}"}])
            combustible = ElementoCatalogo(id=self.repositorio.siguiente_id(), nombre=nombre, descripcion=descripcion)
            self.repositorio.guardar(combustible, Factor(valor=valor, vigente_desde=desde, responsable=responsable,
                                                         fuente=fuente))
            self.db.commit()

        return {"idCombustible": combustible.id, "nombre": combustible.nombre, "estado": api.estado(combustible.estado),
                "factorEmisionKgCO2L": valor, "vigenteDesde": desde.isoformat(), "fuente": fuente}


class ConsultarCombustibles:

    MENSAJE_503 = "No fue posible consultar los combustibles"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = CatalogoRepositorioSQLAlchemy(db, COMBUSTIBLES)

    def ejecutar(self, estado: str | None = None) -> list[dict]:
        estado = v.limpiar(estado).lower() or None
        if estado and v.error_estado(estado):
            raise DatosNoValidos("Los criterios de consulta no son válidos", [v.error_estado(estado)])
        estado = api.estado_interno(estado) if estado else None

        with transaccion(self.db, self.MENSAJE_503):
            combustibles = self.repositorio.listar(estado)
            if not combustibles:
                detalle = f"No hay combustibles {plural_estado(estado)}" if estado else \
                    "No hay combustibles registrados"
                raise NoEncontrado("Sin resultados", [{"campo": "estado", "detalle": detalle}])
            dia = hoy()
            datos = []
            for combustible in combustibles:
                vigente = factor_del_dia(self.repositorio.factores(combustible.id), dia)
                fila = {"idCombustible": combustible.id, "nombre": combustible.nombre,
                        "estado": api.estado(combustible.estado),
                        "factorVigenteKgCO2L": vigente.valor if vigente else None,
                        "fuente": vigente.fuente if vigente else None}
                if vigente is None:
                    fila["sinFactorVigente"] = True
                datos.append(fila)
            return datos
