from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.usuario import Usuario
from app.domain.value_objects.fecha import ahora
from app.repositories.database.modelos import UsuarioModelo


def _a_entidad(m: UsuarioModelo) -> Usuario:
    return Usuario(id_usuario=m.id_usuario, documento=m.documento, nombres=m.nombres, correo=m.correo,
                   telefono=m.telefono, id_sede=m.id_sede, estado=m.estado, fecha_creacion=m.fecha_creacion)


class UsuarioRepositorioSQLAlchemy:

    def __init__(self, sesion: Session):
        self.sesion = sesion

    def _modelo(self, documento: str) -> UsuarioModelo | None:
        return self.sesion.scalar(select(UsuarioModelo).where(UsuarioModelo.documento == documento))

    def buscar_por_documento(self, documento: str) -> Usuario | None:
        modelo = self._modelo(documento)
        return _a_entidad(modelo) if modelo else None

    def buscar_por_correo(self, correo: str) -> Usuario | None:
        modelo = self.sesion.scalar(select(UsuarioModelo).where(func.lower(UsuarioModelo.correo) == correo.lower()))
        return _a_entidad(modelo) if modelo else None

    def siguiente_id(self) -> str:
        ids = self.sesion.scalars(select(UsuarioModelo.id_usuario)).all()
        mayor = max((int(i.split("-")[1]) for i in ids), default=0)
        return f"USR-{mayor + 1:04d}"

    def agregar(self, usuario: Usuario, responsable: str) -> None:
        self.sesion.add(UsuarioModelo(
            id_usuario=usuario.id_usuario, documento=usuario.documento, nombres=usuario.nombres,
            correo=usuario.correo, telefono=usuario.telefono, id_sede=usuario.id_sede,
            estado=usuario.estado, fecha_creacion=usuario.fecha_creacion or ahora(), responsable=responsable,
        ))
        self.sesion.flush()

    def actualizar(self, usuario: Usuario) -> None:
        modelo = self._modelo(usuario.documento)
        modelo.nombres = usuario.nombres
        modelo.correo = usuario.correo
        modelo.telefono = usuario.telefono
        modelo.id_sede = usuario.id_sede
        modelo.estado = usuario.estado
        self.sesion.flush()

    def buscar(self, documento=None, nombre=None, id_sedes=None, estado=None) -> list[Usuario]:
        consulta = select(UsuarioModelo)
        if documento:
            consulta = consulta.where(UsuarioModelo.documento == documento)
        if nombre:
            consulta = consulta.where(func.lower(UsuarioModelo.nombres).contains(nombre.lower()))
        if id_sedes is not None:
            consulta = consulta.where(UsuarioModelo.id_sede.in_(id_sedes))
        if estado:
            consulta = consulta.where(UsuarioModelo.estado == estado)
        consulta = consulta.order_by(UsuarioModelo.nombres)
        return [_a_entidad(m) for m in self.sesion.scalars(consulta)]

    def por_documentos(self, documentos: list[str]) -> list[Usuario]:
        consulta = select(UsuarioModelo).where(UsuarioModelo.documento.in_(documentos)).order_by(UsuarioModelo.nombres)
        return [_a_entidad(m) for m in self.sesion.scalars(consulta)]
