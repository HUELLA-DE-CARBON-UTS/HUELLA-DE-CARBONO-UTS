from app.domain.exceptions.errores import DatosNoValidos, NoEncontrado, ServicioNoDisponible
from app.domain.interfaces.servicio_correo import ServicioCorreo
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import CredencialRepositorioSQLAlchemy
from app.services.contratos.ic13_cerrar_sesiones_usuario import cerrar_sesiones_usuario
from app.services.contratos.ic14_consultar_estado_usuario import consultar_estado_usuario, documento_por_correo
from app.services.seguridad.contrasenas import enmascarar_correo, generar_hash, generar_temporal
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v

MENSAJE_503 = "No fue posible restablecer la contraseña"


class RestablecerContrasena:
    def __init__(self, db, correo: ServicioCorreo):
        self.db = db
        self.correo = correo
        self.credenciales = CredencialRepositorioSQLAlchemy(db)

    def ejecutar(self, documento: str | None, correo: str | None, responsable: str) -> dict:
        documento = "".join((documento or "").split())
        correo = v.limpiar(correo).lower()
        if not documento and not correo:
            raise DatosNoValidos("Los datos del restablecimiento no son válidos", [
                {"field": "document", "detail": "Debe indicar el documento o el correo del usuario"}])

        with transaccion(self.db, MENSAJE_503):
            if not documento:
                documento = documento_por_correo(self.db, correo) or ""
                referencia = f"el correo {correo}"
            else:
                referencia = f"el documento {documento}"
            info = consultar_estado_usuario(self.db, [documento]).get(documento) if documento else None
            if info is None or info["estado"] != "activo" or self.credenciales.buscar(documento) is None:
                raise NoEncontrado("Usuario no encontrado", [
                    {"field": "document", "detail": f"No existe un usuario activo con {referencia}"}])

            temporal = generar_temporal()
            self.credenciales.reemplazar_contrasena(documento, generar_hash(temporal), temporal=True)
            cerradas = cerrar_sesiones_usuario(self.db, documento, "FUN-09")
            HistorialRepositorioSQLAlchemy(self.db).registrar(
                "usuario", documento, "restablecimiento_contrasena", "", "credencial temporal", responsable)

            enviado = self.correo.enviar(
                info["correo"],
                "Restablecimiento de contraseña - Huella de Carbono",
                f"Hola {info['nombres']}:\n\n"
                f"Se restableció su contraseña. Su credencial temporal es: {temporal}\n"
                f"Sirve para un solo ingreso y el sistema le pedirá cambiarla.",
            )
            if not enviado:
                self.db.rollback()
                raise ServicioNoDisponible("No fue posible enviar la credencial temporal", [
                    {"field": "email", "detail": "El servicio de correo (API-EXT-04) no respondió"}])
            self.db.commit()

        return {"document": documento, "destinationEmail": enmascarar_correo(info["correo"]),
                "closedSessions": cerradas, "temporaryCredentialSent": True}
