from typing import Any

from pydantic import BaseModel, Field


class TipoVehiculoEntrada(BaseModel):
    nombre: str | None = Field(None, description="Nombre del tipo de vehículo, por ejemplo «Tractocamión»")
    descripcion: str | None = Field(None, description="Descripción del tipo de vehículo")
    factorConsumoLkm: Any = Field(None, description="Factor de consumo en litros por kilómetro (L/km), mayor que 0")
    fechaInicio: str | None = Field(None, description="Fecha desde la que aplica el factor (AAAA-MM-DD)")

    model_config = {"json_schema_extra": {"examples": [{
        "nombre": "Tractocamión",
        "descripcion": "Camión con remolque para carga pesada",
        "factorConsumoLkm": 0.125,
        "fechaInicio": "2026-11-01",
    }]}}


class FactorConsumoEntrada(BaseModel):
    factorConsumoLkm: Any = Field(None, description="Nuevo factor de consumo en L/km, mayor que 0")
    fechaInicio: str | None = Field(None, description="Fecha desde la que aplica el nuevo factor (AAAA-MM-DD)")

    model_config = {"json_schema_extra": {"examples": [{"factorConsumoLkm": 0.118, "fechaInicio": "2027-01-01"}]}}


class CombustibleEntrada(BaseModel):
    nombre: str | None = Field(None, description="Nombre del combustible, por ejemplo «Diésel»")
    descripcion: str | None = Field(None, description="Descripción del combustible")
    factorEmisionKgCO2L: Any = Field(None, description="Factor de emisión en kg CO₂ por litro, mayor que 0")
    fechaInicio: str | None = Field(None, description="Fecha desde la que aplica el factor (AAAA-MM-DD)")
    fuente: str | None = Field(None, description="Fuente oficial del factor confirmado por el administrador")

    model_config = {"json_schema_extra": {"examples": [{
        "nombre": "Diésel",
        "descripcion": "Combustible diésel para transporte de carga",
        "factorEmisionKgCO2L": 2.6,
        "fechaInicio": "2026-11-01",
        "fuente": "Fuente oficial consultada por API-EXT-03 (valor ilustrativo)",
    }]}}
