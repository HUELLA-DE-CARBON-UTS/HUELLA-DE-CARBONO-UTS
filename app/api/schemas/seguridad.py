from pydantic import BaseModel, Field


class ConfiguracionRolEntrada(BaseModel):
    description: str = Field("", max_length=200, description="Descripción del rol")
    permissions: list[str] = Field(..., description="Operaciones autorizadas (FUN-01 a FUN-65)")

    model_config = {"json_schema_extra": {"examples": [{
        "description": "Consulta consumo, emisiones, indicadores y reportes",
        "permissions": ["FUN-41", "FUN-42", "FUN-49", "FUN-50", "FUN-53", "FUN-54", "FUN-56", "FUN-57", "FUN-61"],
    }]}}
