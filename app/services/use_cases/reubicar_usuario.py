from app.domain.exceptions.errores import DatosNoValidos, NoEncontrado
from app.domain.value_objects.fecha import ahora
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy
from app.services.contratos.ic11_consultar_sede import consultar_sede, error_de_sede
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v

MENSAJE_503 = "No fue posible reubicar al usuario"
SEDE_NO_VALIDA = "La sede de destino no es válida"


class ReubicarUsuario:
    def __init__(self, db):
        self.db = db
        self.usuarios = UsuarioRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, documento: str, sede_destino: str, responsable: str) -> dict:
        documento, sede_destino = documento.strip(), v.limpiar(sede_destino)
        if not sede_destino:
            raise DatosNoValidos("Los datos del traslado no son válidos", [
                {"field": "destinationSite", "detail": "La sede de destino es obligatoria"}])

        with transaccion(self.db, MENSAJE_503):
            usuario = self.usuarios.buscar_por_documento(documento)
            if usuario is None or usuario.estado != "activo":
                raise NoEncontrado("Usuario no encontrado", [
                    {"field": "document", "detail": f"No existe un usuario activo con el documento {documento}"}])

            origen = consultar_sede(self.db, usuario.id_sede) if usuario.id_sede else {"existe": False}
            destino = consultar_sede(self.db, sede_destino)
            error = error_de_sede(destino, sede_destino, "destinationSite")
            if error:
                raise DatosNoValidos(SEDE_NO_VALIDA, [error])
            if destino["idSede"] == usuario.id_sede:
                raise DatosNoValidos(SEDE_NO_VALIDA, [
                    {"field": "destinationSite", "detail": "La sede de destino es la misma sede actual del usuario"}])

            usuario.id_sede = destino["idSede"]
            self.usuarios.actualizar(usuario)
            nombre_origen = origen.get("nombre")
            self.historial.registrar("usuario", documento, "sede", origen.get("idSede") or "", destino["idSede"],
                                     responsable)
            self.db.commit()

        return {"document": documento, "originSite": nombre_origen, "destinationSite": destino["nombre"],
                "transferDate": ahora().date().isoformat()}
