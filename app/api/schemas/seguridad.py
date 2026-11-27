from pydantic import BaseModel, Field


class ConfiguracionRolEntrada(BaseModel):
    descripcion: str = Field("", max_length=200, description="Descripción del rol")
    permisos: list[str] = Field(..., description="Operaciones autorizadas (FUN-01 a FUN-65)")

    model_config = {"json_schema_extra": {"examples": [{
        "descripcion": "Consulta consumo, emisiones, indicadores y reportes",
        "permisos": ["FUN-41", "FUN-42", "FUN-49", "FUN-50", "FUN-53", "FUN-54", "FUN-56", "FUN-57", "FUN-61"],
    }]}}


class IngresoEntrada(BaseModel):
    usuario: str = Field("", description="Correo o documento del usuario")
    contrasena: str = Field("", description="Contraseña")

    model_config = {"json_schema_extra": {"examples": [{"usuario": "1098765432", "contrasena": "********"}]}}


class RestablecimientoEntrada(BaseModel):
    documento: str | None = Field(None, description="Documento del usuario")
    correo: str | None = Field(None, description="Correo del usuario (si no se envía el documento)")

    model_config = {"json_schema_extra": {"examples": [{"documento": "91234567"}]}}


class CambioRolEntrada(BaseModel):
    rol: str = Field("", description="Nuevo rol (nombre o identificador ROL-XX)")

    model_config = {"json_schema_extra": {"examples": [{"rol": "Analista ambiental"}]}}


class InactivacionRolEntrada(BaseModel):
    motivo: str = Field("", description="Motivo de la inactivación")

    model_config = {"json_schema_extra": {"examples": [
        {"motivo": "El cargo se eliminó de la estructura de la empresa"}]}}
