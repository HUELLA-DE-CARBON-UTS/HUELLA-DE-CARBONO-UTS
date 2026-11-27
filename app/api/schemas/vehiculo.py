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
