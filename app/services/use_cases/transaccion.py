from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.exceptions.errores import ErrorNegocio, ServicioNoDisponible

ERROR_BD = [{"field": "database", "detail": "La base de datos no está disponible"}]


@contextmanager
def transaccion(db: Session, mensaje_503: str, conflicto: ErrorNegocio | None = None):
    try:
        yield
    except ErrorNegocio:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        if conflicto is not None:
            raise conflicto from exc
        raise ServicioNoDisponible(mensaje_503, ERROR_BD) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise ServicioNoDisponible(mensaje_503, ERROR_BD) from exc
