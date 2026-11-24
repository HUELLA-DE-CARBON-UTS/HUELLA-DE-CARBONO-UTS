from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import CredencialRepositorioSQLAlchemy
from app.services.contratos.ic12_registrar_credenciales_y_rol import consultar_rol
from app.services.contratos.ic14_consultar_estado_usuario import consultar_estado_usuario
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v


class CambiarRolUsuario:

    MENSAJE_503 = "No fue posible cambiar el rol del usuario"

    def __init__(self, db):
        self.db = db
        self.credenciales = CredencialRepositorioSQLAlchemy(db)

    def ejecutar(self, documento: str, rol: str, responsable: str) -> dict:
        documento, rol = documento.strip(), v.limpiar(rol)
        if not rol:
            raise DatosNoValidos("Los datos del cambio de rol no son válidos", [
                {"field": "role", "detail": "El nuevo rol es obligatorio"}])

        with transaccion(self.db, self.MENSAJE_503):
            info = consultar_estado_usuario(self.db, [documento]).get(documento)
            credencial = self.credenciales.buscar(documento)
            if info is None or info["estado"] != "activo" or credencial is None:
                raise NoEncontrado("Usuario no encontrado", [
                    {"field": "document", "detail": f"No existe un usuario activo con el documento {documento}"}])
            nuevo = consultar_rol(self.db, rol)
            if nuevo is None:
                raise DatosNoValidos("El rol indicado no está disponible", [
                    {"field": "role", "detail": f"El rol {rol} no existe"}])
            if nuevo.estado != "activo":
                raise DatosNoValidos("El rol indicado no está disponible", [
                    {"field": "role", "detail": f"El rol {nuevo.nombre} se encuentra inactivo"}])
            if credencial.id_rol == nuevo.id_rol:
                raise Conflicto("El usuario ya tiene asignado ese rol", [
                    {"field": "role", "detail": f"El usuario {documento} ya tiene el rol {nuevo.nombre}"}])

            self.credenciales.cambiar_rol(documento, nuevo.id_rol)
            HistorialRepositorioSQLAlchemy(self.db).registrar(
                "usuario", documento, "rol", credencial.nombre_rol, nuevo.nombre, responsable)
            self.db.commit()

        return {"document": documento, "previousRole": credencial.nombre_rol, "newRole": nuevo.nombre,
                "appliesFrom": "next_operation"}
