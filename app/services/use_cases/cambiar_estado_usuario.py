from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy
from app.services.contratos.ic13_cerrar_sesiones_usuario import cerrar_sesiones_usuario
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v

MENSAJE_503 = "No fue posible actualizar el estado del usuario"


class CambiarEstadoUsuario:
    def __init__(self, db):
        self.db = db
        self.usuarios = UsuarioRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, documento: str, estado: str, motivo: str, responsable: str) -> dict:
        documento, estado_api, motivo = documento.strip(), v.limpiar(estado).lower(), v.limpiar(motivo)
        errores = []
        if not estado_api:
            errores.append({"field": "status", "detail": "El nuevo estado es obligatorio"})
        elif v.error_estado(estado_api):
            errores.append(v.error_estado(estado_api))
        if not motivo:
            errores.append({"field": "reason", "detail": "El motivo es obligatorio"})
        elif len(motivo) > 300:
            errores.append({"field": "reason", "detail": "El motivo no puede superar 300 caracteres"})
        if errores:
            raise DatosNoValidos("Los datos del cambio de estado no son válidos", errores)
        estado = api.estado_interno(estado_api)

        with transaccion(self.db, MENSAJE_503):
            usuario = self.usuarios.buscar_por_documento(documento)
            if usuario is None:
                raise NoEncontrado("Usuario no encontrado", [
                    {"field": "document", "detail": f"No existe un usuario con el documento {documento}"}])
            if documento == responsable and estado == "inactivo":
                raise Conflicto("No es posible cambiar el estado del usuario", [
                    {"field": "document", "detail": "El administrador no puede inactivarse a sí mismo"}])
            if usuario.estado == estado:
                raise Conflicto("El usuario ya se encuentra en el estado indicado", [
                    {"field": "status", "detail": f"El usuario {documento} ya está {estado}"}])

            anterior = usuario.estado
            usuario.estado = estado
            self.usuarios.actualizar(usuario)
            cerradas = cerrar_sesiones_usuario(self.db, documento, "FUN-03") if estado == "inactivo" else 0
            self.historial.registrar("usuario", documento, "estado", anterior, estado, responsable, motivo)
            self.db.commit()

        return {"document": documento, "previousStatus": api.estado(anterior), "newStatus": api.estado(estado),
                "reason": motivo, "closedSessions": cerradas}
