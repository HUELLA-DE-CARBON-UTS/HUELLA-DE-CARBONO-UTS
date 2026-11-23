from pydantic import BaseModel, Field


class ConfiguracionRolEntrada(BaseModel):
    description: str = Field("", max_length=200, description="Descripción del rol")
    permissions: list[str] = Field(..., description="Operaciones autorizadas (FUN-01 a FUN-65)")

    model_config = {"json_schema_extra": {"examples": [{
        "description": "Consulta consumo, emisiones, indicadores y reportes",
        "permissions": ["FUN-41", "FUN-42", "FUN-49", "FUN-50", "FUN-53", "FUN-54", "FUN-56", "FUN-57", "FUN-61"],
    }]}}


class IngresoEntrada(BaseModel):
    username: str = Field("", description="Correo o documento del usuario")
    password: str = Field("", description="Contraseña")

    model_config = {"json_schema_extra": {"examples": [{"username": "1098765432", "password": "********"}]}}


class RestablecimientoEntrada(BaseModel):
    document: str | None = Field(None, description="Documento del usuario")
    email: str | None = Field(None, description="Correo del usuario (si no se envía el documento)")

    model_config = {"json_schema_extra": {"examples": [{"document": "91234567"}]}}
