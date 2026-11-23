from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repositories.database.modelos import CredencialModelo, RolModelo


def consultar_rol_usuario(db: Session, documentos: list[str]) -> dict[str, str]:
    consulta = (select(CredencialModelo.documento, RolModelo.nombre)
                .join(RolModelo, RolModelo.id_rol == CredencialModelo.id_rol)
                .where(CredencialModelo.documento.in_(list(documentos))))
    return {documento: rol for documento, rol in db.execute(consulta)}
