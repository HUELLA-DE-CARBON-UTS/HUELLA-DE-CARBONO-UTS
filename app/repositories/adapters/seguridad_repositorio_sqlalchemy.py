import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.sesion import Credencial, EventoBitacora, Sesion
from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos import CredencialModelo, EventoBitacoraModelo, SesionModelo
from app.services.seguridad.contrasenas import generar_token, hash_token


class CredencialRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def _modelo(self, documento: str) -> CredencialModelo | None:
        return self.sesion.get(CredencialModelo, documento)

    def buscar(self, documento: str) -> Credencial | None:
        m = self._modelo(documento)
        if m is None:
            return None
        return Credencial(documento=m.documento, hash_contrasena=m.hash_contrasena, temporal=m.temporal,
                          usada=m.usada, id_rol=m.id_rol, nombre_rol=m.rol.nombre, estado_rol=m.rol.estado)

    def crear(self, documento: str, hash_contrasena: str, temporal: bool, id_rol: str) -> None:
        self.sesion.add(CredencialModelo(documento=documento, hash_contrasena=hash_contrasena, temporal=temporal,
                                         usada=False, id_rol=id_rol, fecha_actualizacion=ahora()))
        self.sesion.flush()

    def marcar_usada(self, documento: str) -> None:
        m = self._modelo(documento)
        m.usada = True
        m.fecha_actualizacion = ahora()
        self.sesion.flush()


def _sesion(m: SesionModelo) -> Sesion:
    return Sesion(id_sesion=m.id_sesion, documento=m.documento, estado=m.estado,
                  requiere_cambio_contrasena=m.requiere_cambio_contrasena, fecha_ingreso=m.fecha_ingreso,
                  ultima_actividad=m.ultima_actividad, fecha_salida=m.fecha_salida)


class SesionRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def _nuevo_id(self) -> str:
        while True:
            id_sesion = f"SES-{secrets.token_hex(3).upper()}"
            if self.sesion.get(SesionModelo, id_sesion) is None:
                return id_sesion

    def crear(self, documento: str, requiere_cambio: bool) -> tuple[Sesion, str]:
        token = generar_token()
        momento = ahora()
        modelo = SesionModelo(id_sesion=self._nuevo_id(), token_hash=hash_token(token), documento=documento,
                              estado="vigente", requiere_cambio_contrasena=requiere_cambio,
                              fecha_ingreso=momento, ultima_actividad=momento)
        self.sesion.add(modelo)
        self.sesion.flush()
        return _sesion(modelo), token

    def buscar_por_token(self, token: str) -> Sesion | None:
        m = self.sesion.scalar(select(SesionModelo).where(SesionModelo.token_hash == hash_token(token)))
        return _sesion(m) if m else None


class BitacoraRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def registrar(self, evento: EventoBitacora) -> None:
        self.sesion.add(EventoBitacoraModelo(usuario=evento.usuario, tipo_evento=evento.tipo_evento,
                                             operacion=evento.operacion, id_sesion=evento.id_sesion,
                                             fecha=evento.fecha))
        self.sesion.flush()
