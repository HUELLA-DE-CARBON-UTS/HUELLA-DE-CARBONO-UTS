"""Fecha y hora del sistema en la zona horaria de Colombia (UTC-05:00)."""

from datetime import datetime, timedelta, timezone

ZONA_COLOMBIA = timezone(timedelta(hours=-5))


def ahora() -> datetime:
    return datetime.now(ZONA_COLOMBIA).replace(microsecond=0)
