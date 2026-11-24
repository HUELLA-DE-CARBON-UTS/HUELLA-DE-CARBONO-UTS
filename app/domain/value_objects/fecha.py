from datetime import datetime, timedelta, timezone

ZONA_COLOMBIA = timezone(timedelta(hours=-5))


def ahora() -> datetime:
    return datetime.now(ZONA_COLOMBIA).replace(microsecond=0)


def en_colombia(valor: datetime | None) -> datetime | None:
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=ZONA_COLOMBIA)
    return valor.astimezone(ZONA_COLOMBIA)


def texto(valor: datetime | None) -> str | None:
    valor = en_colombia(valor)
    return valor.replace(microsecond=0).isoformat() if valor else None
