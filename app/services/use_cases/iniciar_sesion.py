from app.domain.entities.sesion import EventoBitacora
from app.domain.exceptions.errores import DatosNoValidos, PermisoDenegado, SesionNoValida
from app.domain.value_objects.fecha import ahora
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import (
    BitacoraRepositorioSQLAlchemy, CredencialRepositorioSQLAlchemy, SesionRepositorioSQLAlchemy)
from app.services.contratos.ic14_consultar_estado_usuario import consultar_estado_usuario, documento_por_correo
from app.services.seguridad.contrasenas import HASH_REFERENCIA, verificar
from app.services.use_cases.transaccion import transaccion

MENSAJE_503 = "No fue posible iniciar la sesión"


def credenciales_incorrectas() -> SesionNoValida:
    return SesionNoValida("Usuario o contraseña incorrectos", [
        {"campo": "credenciales", "detalle": "Las credenciales no coinciden"}])


class IniciarSesion:
    def __init__(self, db):
        self.db = db
        self.credenciales = CredencialRepositorioSQLAlchemy(db)
        self.sesiones = SesionRepositorioSQLAlchemy(db)
        self.bitacora = BitacoraRepositorioSQLAlchemy(db)

    def ejecutar(self, usuario: str, contrasena: str) -> tuple[dict, str]:
        usuario = (usuario or "").strip()
        contrasena = contrasena or ""
        errores = []
        if not usuario:
            errores.append({"campo": "usuario", "detalle": "El usuario es obligatorio"})
        if not contrasena:
            errores.append({"campo": "contrasena", "detalle": "La contraseña es obligatoria"})
        if errores:
            raise DatosNoValidos("Los datos de ingreso no son válidos", errores)

        with transaccion(self.db, MENSAJE_503):
            documento = documento_por_correo(self.db, usuario) if "@" in usuario else usuario
            credencial = self.credenciales.buscar(documento) if documento else None
            if credencial is None:
                verificar(contrasena, HASH_REFERENCIA)
                self._fallido(usuario)
                raise credenciales_incorrectas()

            temporal_ya_usada = credencial.temporal and credencial.usada
            if temporal_ya_usada or not verificar(contrasena, credencial.hash_contrasena):
                self._fallido(documento)
                raise credenciales_incorrectas()

            info = consultar_estado_usuario(self.db, [documento]).get(documento)
            if info is None or info["estado"] != "activo":
                self._fallido(documento)
                raise PermisoDenegado("El usuario no puede ingresar al sistema", [
                    {"campo": "usuario", "detalle": "El usuario se encuentra inactivo"}])

            if credencial.temporal:
                self.credenciales.marcar_usada(documento)
            sesion, token = self.sesiones.crear(documento, requiere_cambio=credencial.temporal)
            self.bitacora.registrar(EventoBitacora(usuario=documento, tipo_evento="ingreso", operacion="FUN-06",
                                                   fecha=sesion.fecha_ingreso, id_sesion=sesion.id_sesion))
            self.db.commit()

        datos = {"idSesion": sesion.id_sesion, "usuario": documento, "rol": credencial.nombre_rol,
                 "sede": info["sede"], "requiereCambioContrasena": credencial.temporal}
        return datos, token

    def _fallido(self, usuario: str) -> None:
        self.bitacora.registrar(EventoBitacora(usuario=usuario, tipo_evento="intento_fallido",
                                               operacion="FUN-06", fecha=ahora()))
        self.db.commit()
