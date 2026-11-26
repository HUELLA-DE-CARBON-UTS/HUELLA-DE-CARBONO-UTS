import re

from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado, SolicitudIncorrecta
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import CredencialRepositorioSQLAlchemy
from app.services.contratos.ic12_registrar_credenciales_y_rol import consultar_rol
from app.services.contratos.ic14_consultar_estado_usuario import consultar_estado_usuario
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v

FORMATO_ID_ROL = re.compile(r"^ROL-\d{2,}$")


def validar_id_rol(id_rol: str) -> str:
    id_rol = id_rol.strip().upper()
    if not FORMATO_ID_ROL.match(id_rol):
        raise SolicitudIncorrecta("El identificador del rol no es válido", [
            {"field": "roleId", "detail": "Debe tener el formato ROL-XX"}])
    return id_rol


def contar_usuarios_activos(db, id_rol: str) -> int:
    documentos = CredencialRepositorioSQLAlchemy(db).documentos_con_rol(id_rol)
    if not documentos:
        return 0
    estados = consultar_estado_usuario(db, documentos)
    return sum(1 for d in documentos if estados.get(d, {}).get("estado") == "activo")


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


class ConsultarRoles:

    MENSAJE_503 = "No fue posible consultar los roles"

    def __init__(self, db):
        self.db = db

    def ejecutar(self, estado: str | None = None) -> list[dict]:
        estado = v.limpiar(estado).lower() or None
        if estado and v.error_estado(estado):
            raise DatosNoValidos("Los criterios de consulta no son válidos", [v.error_estado(estado)])
        estado = api.estado_interno(estado) if estado else None

        with transaccion(self.db, self.MENSAJE_503):
            roles = RolRepositorioSQLAlchemy(self.db).listar(estado)
            if not roles:
                detalle = f"No hay roles en estado {estado}" if estado else "No hay roles registrados"
                raise NoEncontrado("Sin resultados", [{"field": "status", "detail": detalle}])
            return [{"roleId": r.id_rol, "name": r.nombre, "status": api.estado(r.estado), "permissions": r.permisos,
                     "activeUsers": contar_usuarios_activos(self.db, r.id_rol)} for r in roles]


class InactivarRol:

    MENSAJE_503 = "No fue posible inactivar el rol"

    def __init__(self, db):
        self.db = db
        self.roles = RolRepositorioSQLAlchemy(db)

    def ejecutar(self, id_rol: str, motivo: str, responsable: str) -> dict:
        id_rol = validar_id_rol(id_rol)
        motivo = v.limpiar(motivo)
        if not motivo:
            raise DatosNoValidos("Los datos de la inactivación no son válidos", [
                {"field": "reason", "detail": "El motivo es obligatorio"}])
        if len(motivo) > 300:
            raise DatosNoValidos("Los datos de la inactivación no son válidos", [
                {"field": "reason", "detail": "El motivo no puede superar 300 caracteres"}])

        with transaccion(self.db, self.MENSAJE_503):
            rol = self.roles.buscar_por_id(id_rol)
            if rol is None or rol.estado != "activo":
                raise NoEncontrado("Rol no encontrado", [
                    {"field": "roleId", "detail": f"No existe un rol activo con el identificador {id_rol}"}])
            activos = contar_usuarios_activos(self.db, id_rol)
            if activos:
                texto_usuarios = "1 usuario activo" if activos == 1 else f"{activos} usuarios activos"
                raise Conflicto("El rol tiene usuarios activos asignados", [
                    {"field": "roleId", "detail": f"El rol {id_rol} tiene {texto_usuarios}"}])

            rol = self.roles.cambiar_estado(id_rol, "inactivo", responsable)
            HistorialRepositorioSQLAlchemy(self.db).registrar("rol", id_rol, "estado", "activo", "inactivo",
                                                              responsable, motivo)
            self.db.commit()

        return {"roleId": rol.id_rol, "name": rol.nombre, "status": api.estado(rol.estado), "reason": motivo}
