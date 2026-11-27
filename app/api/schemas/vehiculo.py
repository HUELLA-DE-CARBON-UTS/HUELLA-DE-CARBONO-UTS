from typing import Any

from pydantic import BaseModel, Field


class VehiculoEntrada(BaseModel):
    placa: str | None = Field(None, description="Placa con el formato AAA-000")
    tipoVehiculo: str | None = Field(None, description="Nombre o identificador (TV-XX) del tipo de vehículo")
    combustible: str | None = Field(None, description="Nombre o identificador (CB-XX) del combustible")
    capacidadT: Any = Field(None, description="Capacidad de carga en toneladas, mayor que 0")
    sede: str | None = Field(None, description="Nombre o identificador (SED-XX) de la sede")

    model_config = {"json_schema_extra": {"examples": [{
        "placa": "TTK-482",
        "tipoVehiculo": "Tractocamión",
        "combustible": "Diésel",
        "capacidadT": 34,
        "sede": "Bucaramanga",
    }]}}


class FichaTecnicaEntrada(BaseModel):
    tipoVehiculo: str | None = Field(None, description="Nuevo tipo de vehículo (nombre o TV-XX)")
    combustible: str | None = Field(None, description="Nuevo combustible (nombre o CB-XX)")
    capacidadT: Any = Field(None, description="Nueva capacidad de carga en toneladas, mayor que 0")
    aplicaDesde: str | None = Field(None, description="Fecha desde la que aplica el cambio (AAAA-MM-DD)")

    model_config = {"json_schema_extra": {"examples": [{"combustible": "Gas natural vehicular", "aplicaDesde": "2026-11-10"}]}}


class EstadoSedeVehiculoEntrada(BaseModel):
    estado: str | None = Field(None, description='"disponible" o "fuera de servicio"')
    sede: str | None = Field(None, description="Nombre o identificador (SED-XX) de la nueva sede")

    model_config = {"json_schema_extra": {"examples": [{"estado": "fuera de servicio"}]}}
