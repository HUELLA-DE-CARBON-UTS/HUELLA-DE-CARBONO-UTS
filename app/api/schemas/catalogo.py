from typing import Any

from pydantic import BaseModel, Field


class TipoVehiculoEntrada(BaseModel):
    name: str | None = Field(None, description="Nombre del tipo de vehículo, por ejemplo «Tractocamión»")
    description: str | None = Field(None, description="Descripción del tipo de vehículo")
    consumptionFactorLkm: Any = Field(None, description="Factor de consumo en litros por kilómetro (L/km), mayor que 0")
    startDate: str | None = Field(None, description="Fecha desde la que aplica el factor (AAAA-MM-DD)")

    model_config = {"json_schema_extra": {"examples": [{
        "name": "Tractocamión",
        "description": "Camión con remolque para carga pesada",
        "consumptionFactorLkm": 0.125,
        "startDate": "2026-11-01",
    }]}}


class FactorConsumoEntrada(BaseModel):
    consumptionFactorLkm: Any = Field(None, description="Nuevo factor de consumo en L/km, mayor que 0")
    startDate: str | None = Field(None, description="Fecha desde la que aplica el nuevo factor (AAAA-MM-DD)")

    model_config = {"json_schema_extra": {"examples": [{"consumptionFactorLkm": 0.118, "startDate": "2027-01-01"}]}}
