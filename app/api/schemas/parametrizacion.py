from pydantic import BaseModel, Field


class SedeEntrada(BaseModel):
    name: str = Field("", description="Nombre de la sede")
    city: str = Field("", description="Ciudad donde funciona la sede")
    address: str = Field("", description="Dirección de la sede")
    manager: str = Field("", description="Nombre de la persona responsable de la sede")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Barranquilla",
                "city": "Barranquilla",
                "address": "Calle 30 # 1-25, zona industrial",
                "manager": "Carolina Herrera Pérez",
            }]
        }
    }
