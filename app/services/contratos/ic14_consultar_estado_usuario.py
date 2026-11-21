from sqlalchemy.orm import Session

from app.repositories.adapters.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy
from app.services.contratos.ic11_consultar_sede import nombres_de_sedes


def consultar_estado_usuario(db: Session, documentos: list[str]) -> dict[str, dict]:
    usuarios = UsuarioRepositorioSQLAlchemy(db).por_documentos(list(documentos))
    sedes = nombres_de_sedes(db, [u.id_sede for u in usuarios])
    return {
        u.documento: {"estado": u.estado, "nombres": u.nombres, "sede": sedes.get(u.id_sede),
                      "correo": u.correo}
        for u in usuarios
    }


def documento_por_correo(db: Session, correo: str) -> str | None:
    usuario = UsuarioRepositorioSQLAlchemy(db).buscar_por_correo(correo)
    return usuario.documento if usuario else None
