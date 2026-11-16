from pydantic import BaseModel, Field


class SedeEntrada(BaseModel):
    nombre: str = Field("", description="Nombre de la sede")
    ciudad: str = Field("", description="Ciudad donde funciona la sede")
    direccion: str = Field("", description="Dirección de la sede")
    responsable: str = Field("", description="Nombre de la persona responsable de la sede")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "nombre": "Barranquilla",
                "ciudad": "Barranquilla",
                "direccion": "Calle 30 # 1-25, zona industrial",
                "responsable": "Carolina Herrera Pérez",
            }]
        }
    }


class SedeSalida(BaseModel):
    idSede: str
    nombre: str
    ciudad: str
    direccion: str
    responsable: str
    estado: str
