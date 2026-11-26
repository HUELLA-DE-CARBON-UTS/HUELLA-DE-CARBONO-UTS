import secrets
from datetime import datetime

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

    def reemplazar_contrasena(self, documento: str, hash_contrasena: str, temporal: bool) -> None:
        m = self._modelo(documento)
        m.hash_contrasena = hash_contrasena
        m.temporal = temporal
        m.usada = False
        m.fecha_actualizacion = ahora()
        self.sesion.flush()

    def marcar_usada(self, documento: str) -> None:
        m = self._modelo(documento)
        m.usada = True
        m.fecha_actualizacion = ahora()
        self.sesion.flush()

    def cambiar_rol(self, documento: str, id_rol: str) -> None:
        m = self._modelo(documento)
        m.id_rol = id_rol
        m.fecha_actualizacion = ahora()
        self.sesion.flush()
        self.sesion.expire(m, ["rol"])

    def documentos_con_rol(self, id_rol: str) -> list[str]:
        return list(self.sesion.scalars(select(CredencialModelo.documento).where(CredencialModelo.id_rol == id_rol)))


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

    def buscar(self, id_sesion: str) -> Sesion | None:
        m = self.sesion.get(SesionModelo, id_sesion)
        return _sesion(m) if m else None

    def buscar_por_token(self, token: str) -> Sesion | None:
        m = self.sesion.scalar(select(SesionModelo).where(SesionModelo.token_hash == hash_token(token)))
        return _sesion(m) if m else None

    def registrar_actividad(self, id_sesion: str) -> None:
        self.sesion.get(SesionModelo, id_sesion).ultima_actividad = ahora()
        self.sesion.flush()

    def finalizar(self, id_sesion: str) -> datetime:
        m = self.sesion.get(SesionModelo, id_sesion)
        m.estado = "finalizada"
        m.fecha_salida = ahora()
        self.sesion.flush()
        return m.fecha_salida

    def vigentes_de(self, documento: str) -> list[Sesion]:
        consulta = select(SesionModelo).where(SesionModelo.documento == documento, SesionModelo.estado == "vigente")
        return [_sesion(m) for m in self.sesion.scalars(consulta)]


class BitacoraRepositorioSQLAlchemy:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def registrar(self, evento: EventoBitacora) -> None:
        self.sesion.add(EventoBitacoraModelo(usuario=evento.usuario, tipo_evento=evento.tipo_evento,
                                             operacion=evento.operacion, id_sesion=evento.id_sesion,
                                             fecha=evento.fecha))
        self.sesion.flush()

    def consultar(self, desde: datetime, hasta: datetime, usuario: str | None = None,
                  tipo_evento: str | None = None) -> list[EventoBitacora]:
        consulta = select(EventoBitacoraModelo).where(EventoBitacoraModelo.fecha >= desde,
                                                      EventoBitacoraModelo.fecha < hasta)
        if usuario:
            consulta = consulta.where(EventoBitacoraModelo.usuario == usuario)
        if tipo_evento:
            consulta = consulta.where(EventoBitacoraModelo.tipo_evento == tipo_evento)
        consulta = consulta.order_by(EventoBitacoraModelo.fecha.desc(), EventoBitacoraModelo.id.desc())
        return [EventoBitacora(usuario=m.usuario, tipo_evento=m.tipo_evento, operacion=m.operacion,
                               fecha=m.fecha, id_sesion=m.id_sesion) for m in self.sesion.scalars(consulta)]
