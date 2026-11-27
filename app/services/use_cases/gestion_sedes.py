import unicodedata

from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.sede_repositorio_sqlalchemy import SedeRepositorioSQLAlchemy
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion
from app.services.validators import sede_validador

ESTADOS_SEDE = ("active", "inactive")


def _orden(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


class ActualizarSede:

    MENSAJE_503 = "No fue posible actualizar la sede"

    def __init__(self, db):
        self.db = db
        self.sedes = SedeRepositorioSQLAlchemy(db)

    def ejecutar(self, id_sede: str, cambios: dict[str, str | None], responsable: str) -> dict:
        id_sede = id_sede.strip().upper()
        enviados = {campo: sede_validador.limpiar(valor) for campo, valor in cambios.items() if valor is not None}
        if not enviados:
            raise DatosNoValidos("Los datos de la sede no son válidos", [
                {"field": "data", "detail": "Debe indicar al menos un dato para modificar"}])
        errores = []
        for campo, valor in enviados.items():
            maximo = sede_validador.CAMPOS[campo][1]
            if not valor:
                errores.append({"field": sede_validador.CAMPOS_API[campo], "detail": "El campo modificado no puede quedar vacío"})
            elif len(valor) > maximo:
                errores.append({"field": sede_validador.CAMPOS_API[campo], "detail": f"El campo no puede superar {maximo} caracteres"})
        if errores:
            raise DatosNoValidos("Los datos de la sede no son válidos", errores)

        with transaccion(self.db, self.MENSAJE_503):
            sede = self.sedes.buscar_por_id(id_sede)
            if sede is None or sede.estado != "activa":
                raise NoEncontrado("Sede no encontrada", [
                    {"field": "siteId", "detail": f"No existe una sede activa con el identificador {id_sede}"}])
            nombre = enviados.get("nombre", sede.nombre)
            ciudad = enviados.get("ciudad", sede.ciudad)
            if ("nombre" in enviados or "ciudad" in enviados) and self.sedes.existe_en_ciudad(nombre, ciudad, id_sede):
                raise Conflicto("Ya existe una sede con ese nombre en la ciudad", [
                    {"field": "name", "detail": f"El nombre {nombre} ya lo usa otra sede de la ciudad"}])

            direccion_anterior = sede.direccion
            historial = HistorialRepositorioSQLAlchemy(self.db)
            for campo, valor in enviados.items():
                anterior = getattr(sede, campo)
                if valor != anterior:
                    historial.registrar("sede", id_sede, campo, anterior, valor, responsable)
                    setattr(sede, campo, valor)
            sede = self.sedes.actualizar(sede)
            self.db.commit()

        return {"siteId": sede.id_sede, "name": sede.nombre, "previousAddress": direccion_anterior,
                "newAddress": sede.direccion, "manager": sede.responsable}


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
