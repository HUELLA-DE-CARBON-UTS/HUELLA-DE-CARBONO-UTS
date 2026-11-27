from pydantic import BaseModel, Field


class RecorridoEntrada(BaseModel):
    placa: str | None = Field(None, description="Placa de un vehículo disponible, formato AAA-000")
    origen: str | None = Field(None, description="Ciudad o dirección de origen")
    destino: str | None = Field(None, description="Ciudad o dirección de destino, distinta del origen")
    fechaProgramada: str | None = Field(None, description="Fecha del recorrido (AAAA-MM-DD), no anterior a hoy")

    model_config = {"json_schema_extra": {"examples": [{
        "placa": "TTK-482", "origen": "Bucaramanga", "destino": "Barranquilla", "fechaProgramada": "2026-12-18"}]}}


class ReprogramacionEntrada(BaseModel):
    fechaProgramada: str | None = Field(None, description="Nueva fecha (AAAA-MM-DD), no anterior a hoy")
    placa: str | None = Field(None, description="Placa del nuevo vehículo, que debe estar disponible")

    model_config = {"json_schema_extra": {"examples": [{"placa": "WFN-731", "fechaProgramada": "2026-12-20"}]}}


class CancelacionEntrada(BaseModel):
    motivo: str | None = Field(None, description="Motivo de la cancelación")

    model_config = {"json_schema_extra": {"examples": [{"motivo": "El cliente aplazó el despacho"}]}}
