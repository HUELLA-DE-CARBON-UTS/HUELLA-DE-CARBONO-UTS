"""Esquemas de entrada y salida del módulo MOD-02 Gestión de Seguridad."""

from pydantic import BaseModel, Field


class ConfiguracionRolEntrada(BaseModel):
    descripcion: str = Field("", max_length=200, description="Descripción del rol")
    permisos: list[str] = Field(..., description="Operaciones autorizadas (FUN-01 a FUN-65)")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "descripcion": "Consulta consumo, emisiones, indicadores y reportes",
                "permisos": ["FUN-41", "FUN-42", "FUN-49", "FUN-50", "FUN-53", "FUN-54", "FUN-56", "FUN-57", "FUN-61"],
            }]
        }
    }


class RolSalida(BaseModel):
    idRol: str
    nombre: str
    descripcion: str
    estado: str
    permisos: list[str]
    accion: str
