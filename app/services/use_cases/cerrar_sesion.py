import re
from datetime import timedelta

from app.domain.entities.sesion import EventoBitacora, Sesion
from app.domain.exceptions.errores import NoEncontrado, PermisoDenegado, SolicitudIncorrecta
from app.domain.value_objects.fecha import ahora, en_colombia, texto
from app.repositories.adapters.seguridad_repositorio_sqlalchemy import (
    BitacoraRepositorioSQLAlchemy, SesionRepositorioSQLAlchemy)
from app.repositories.config.settings import settings
from app.services.use_cases.transaccion import transaccion

MENSAJE_503 = "No fue posible cerrar la sesión"
FORMATO_ID_SESION = re.compile(r"^SES-[0-9A-F]{6}$")


class CerrarSesion:
    def __init__(self, db):
        self.db = db
        self.sesiones = SesionRepositorioSQLAlchemy(db)

    def ejecutar(self, id_sesion: str, sesion_del_token: Sesion) -> dict:
        id_sesion = id_sesion.strip().upper()
        if not FORMATO_ID_SESION.match(id_sesion):
            raise SolicitudIncorrecta("El identificador de la sesión no es válido", [
                {"campo": "idSesion", "detalle": "Debe tener el formato SES-XXXXXX"}])
        if sesion_del_token.id_sesion != id_sesion:
            raise PermisoDenegado("No puede cerrar esta sesión", [
                {"campo": "idSesion", "detalle": "Solo puede cerrar la sesión a la que pertenece el token enviado"}])

        with transaccion(self.db, MENSAJE_503):
            sesion = self.sesiones.buscar(id_sesion)
            if sesion is None or sesion.estado != "vigente":
                raise NoEncontrado("Sesión no encontrada", [
                    {"campo": "idSesion", "detalle": f"La sesión {id_sesion} ya fue finalizada"}])
            limite = en_colombia(sesion.ultima_actividad) + timedelta(minutes=settings.access_token_expire_minutes)
            vencida = ahora() > limite
            fecha_salida = self.sesiones.finalizar(id_sesion)
            BitacoraRepositorioSQLAlchemy(self.db).registrar(EventoBitacora(
                usuario=sesion.documento, tipo_evento="salida", operacion="FUN-08", fecha=fecha_salida,
                id_sesion=id_sesion))
            self.db.commit()
            if vencida:
                raise NoEncontrado("Sesión no encontrada", [
                    {"campo": "idSesion", "detalle": f"La sesión {id_sesion} ya no estaba vigente por inactividad"}])

        return {"idSesion": id_sesion, "fechaSalida": texto(fecha_salida)}
