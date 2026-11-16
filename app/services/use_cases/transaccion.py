"""Manejo común de la transacción en los casos de uso."""

from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.exceptions.errores import ErrorNegocio, ServicioNoDisponible

ERROR_BD = [{"campo": "baseDeDatos", "detalle": "La base de datos no está disponible"}]


@contextmanager
def transaccion(db: Session, mensaje_503: str, conflicto: ErrorNegocio | None = None):
    """Deshace los cambios si algo falla.

    - Un error de negocio se deja pasar tal cual.
    - Una violación de unicidad se convierte en `conflicto` si se indicó (dos
      solicitudes que registran lo mismo al tiempo).
    - Cualquier otro error de la base de datos se convierte en 503 con el mensaje de la historia.
    """
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
