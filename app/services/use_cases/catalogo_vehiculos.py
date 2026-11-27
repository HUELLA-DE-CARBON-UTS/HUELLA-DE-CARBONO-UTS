from sqlalchemy.orm import Session

from app.domain.entities.catalogo import ElementoCatalogo, Factor
from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.catalogo_repositorio_sqlalchemy import TIPOS_VEHICULO, CatalogoRepositorioSQLAlchemy
from app.services.mappers import api
from app.services.use_cases.catalogo_comun import factor_del_dia, hoy, plural_estado, reemplazar_factor
from app.services.use_cases.transaccion import transaccion
from app.services.validators import catalogo_validador as v

CAMPO_FACTOR = "consumptionFactorLkm"


def _no_encontrado(identificador: str, activo: bool) -> NoEncontrado:
    detalle = "un tipo activo" if activo else "un tipo"
    return NoEncontrado("Tipo de vehículo no encontrado", [
        {"field": "typeId", "detail": f"No existe {detalle} con el identificador {identificador}"}])


class RegistrarTipoVehiculo:

    MENSAJE_503 = "No fue posible registrar el tipo de vehículo"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = CatalogoRepositorioSQLAlchemy(db, TIPOS_VEHICULO)

    def ejecutar(self, nombre, descripcion, factor, fecha_inicio, responsable: str) -> dict:
        nombre, descripcion = v.limpiar(nombre), v.limpiar(descripcion)
        valor, desde = v.numero(factor), v.fecha(fecha_inicio)
        v.lanzar([
            v.error_texto("name", nombre, "El nombre del tipo de vehículo es obligatorio", 60),
            v.error_texto("description", descripcion, "La descripción es obligatoria", 200),
            None if valor is not None and valor > 0 else
            {"field": CAMPO_FACTOR, "detail": "Debe ser numérico, mayor que 0 y expresado en L/km"},
            v.error_fecha("startDate", desde),
        ], "Los datos del tipo de vehículo no son válidos", CAMPO_FACTOR, "El factor de consumo no es válido")

        duplicado = Conflicto("El tipo de vehículo ya está registrado", [
            {"field": "name", "detail": f"Ya existe el tipo {nombre}"}])
        with transaccion(self.db, self.MENSAJE_503, duplicado):
            existente = self.repositorio.buscar_por_nombre(nombre)
            if existente is not None:
                raise Conflicto("El tipo de vehículo ya está registrado", [
                    {"field": "name", "detail": f"Ya existe el tipo {existente.nombre}"}])
            tipo = ElementoCatalogo(id=self.repositorio.siguiente_id(), nombre=nombre, descripcion=descripcion)
            self.repositorio.guardar(tipo, Factor(valor=valor, vigente_desde=desde, responsable=responsable))
            self.db.commit()

        return {"typeId": tipo.id, "name": tipo.nombre, "status": api.estado(tipo.estado),
                "consumptionFactorLkm": valor, "validFrom": desde.isoformat()}


class ActualizarFactorConsumo:

    MENSAJE_503 = "No fue posible actualizar el factor de consumo"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = CatalogoRepositorioSQLAlchemy(db, TIPOS_VEHICULO)

    def ejecutar(self, id_tipo: str, factor, fecha_inicio, responsable: str) -> dict:
        id_tipo = (id_tipo or "").strip().upper()
        valor, desde = v.numero(factor), v.fecha(fecha_inicio)
        error_factor = None
        if valor is None:
            error_factor = {"field": CAMPO_FACTOR, "detail": "Debe ser numérico y mayor que 0"}
        elif valor <= 0:
            error_factor = {"field": CAMPO_FACTOR, "detail": "Debe ser mayor que 0"}
        v.lanzar([error_factor, v.error_fecha("startDate", desde)],
                 "Los datos del nuevo factor no son válidos", CAMPO_FACTOR, "El factor de consumo no es válido")

        with transaccion(self.db, self.MENSAJE_503):
            tipo = self.repositorio.buscar(id_tipo)
            if tipo is None or tipo.estado != "activo":
                raise _no_encontrado(id_tipo, True)
            nuevo = Factor(valor=valor, vigente_desde=desde, responsable=responsable)
            anterior = reemplazar_factor(self.repositorio, id_tipo, nuevo)
            self.db.commit()

        return {
            "typeId": id_tipo,
            "previousFactor": {"valueLkm": anterior.valor, "validTo": anterior.vigente_hasta.isoformat()}
            if anterior else None,
            "newFactor": {"valueLkm": valor, "validFrom": desde.isoformat()},
        }


class ConsultarTiposVehiculo:

    MENSAJE_503 = "No fue posible consultar los tipos de vehículo"

    def __init__(self, db: Session):
        self.db = db
        self.repositorio = CatalogoRepositorioSQLAlchemy(db, TIPOS_VEHICULO)

    def ejecutar(self, estado: str | None = None) -> list[dict]:
        estado = v.limpiar(estado).lower() or None
        if estado and v.error_estado(estado):
            raise DatosNoValidos("Los criterios de consulta no son válidos", [v.error_estado(estado)])
        estado = api.estado_interno(estado) if estado else None

        with transaccion(self.db, self.MENSAJE_503):
            tipos = self.repositorio.listar(estado)
            if not tipos:
                detalle = f"No hay tipos de vehículo {plural_estado(estado)}" if estado else \
                    "No hay tipos de vehículo registrados"
                raise NoEncontrado("Sin resultados", [{"field": "status", "detail": detalle}])
            dia = hoy()
            datos = []
            for tipo in tipos:
                vigente = factor_del_dia(self.repositorio.factores(tipo.id), dia)
                fila = {"typeId": tipo.id, "name": tipo.nombre, "status": api.estado(tipo.estado),
                        "currentFactorLkm": vigente.valor if vigente else None}
                if vigente is None:
                    fila["noCurrentFactor"] = True
                datos.append(fila)
            return datos
