from app.domain.exceptions.errores import Conflicto, DatosNoValidos, NoEncontrado
from app.repositories.adapters.historial_repositorio_sqlalchemy import HistorialRepositorioSQLAlchemy
from app.repositories.adapters.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v

MENSAJE_503 = "No fue posible actualizar los datos de contacto"
CORREO_OCUPADO = "El correo ya pertenece a otro usuario"


class ActualizarContacto:
    def __init__(self, db):
        self.db = db
        self.usuarios = UsuarioRepositorioSQLAlchemy(db)
        self.historial = HistorialRepositorioSQLAlchemy(db)

    def ejecutar(self, documento: str, correo: str | None, telefono: str | None, responsable: str) -> dict:
        documento = documento.strip()
        if correo is None and telefono is None:
            raise DatosNoValidos("Los datos de contacto no son válidos", [
                {"campo": "correo", "detalle": "Debe indicar el correo o el teléfono nuevos"}])
        correo = v.limpiar(correo).lower() if correo is not None else None
        telefono = "".join(telefono.split()) if telefono is not None else None
        errores = []
        if correo is not None and v.error_correo(correo):
            errores.append(v.error_correo(correo))
        if telefono is not None and v.error_telefono(telefono):
            errores.append(v.error_telefono(telefono))
        if errores:
            raise DatosNoValidos("Los datos de contacto no son válidos", errores)

        conflicto = Conflicto(CORREO_OCUPADO, [{"campo": "correo", "detalle": f"El correo {correo} ya está registrado"}])
        with transaccion(self.db, MENSAJE_503, conflicto):
            usuario = self.usuarios.buscar_por_documento(documento)
            if usuario is None or usuario.estado != "activo":
                raise NoEncontrado("Usuario no encontrado", [
                    {"campo": "documento", "detalle": f"No existe un usuario activo con el documento {documento}"}])
            if correo is not None:
                otro = self.usuarios.buscar_por_correo(correo)
                if otro and otro.documento != documento:
                    raise Conflicto(CORREO_OCUPADO, [
                        {"campo": "correo", "detalle": f"El correo {correo} está asignado al usuario {otro.documento}"}])

            correo_anterior, telefono_anterior = usuario.correo, usuario.telefono
            if correo is not None and correo != correo_anterior:
                usuario.correo = correo
                self.historial.registrar("usuario", documento, "correo", correo_anterior, correo, responsable)
            if telefono is not None and telefono != telefono_anterior:
                usuario.telefono = telefono
                self.historial.registrar("usuario", documento, "telefono", telefono_anterior, telefono, responsable)
            self.usuarios.actualizar(usuario)
            self.db.commit()

        return {"documento": documento, "correoAnterior": correo_anterior, "correoNuevo": usuario.correo,
                "telefono": usuario.telefono}
