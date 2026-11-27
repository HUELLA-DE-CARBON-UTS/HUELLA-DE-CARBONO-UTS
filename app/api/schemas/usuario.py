from pydantic import BaseModel, Field


class RegistroUsuarioEntrada(BaseModel):
    documento: str = Field("", description="Documento de identidad, solo dígitos")
    nombres: str = Field("", description="Nombres y apellidos")
    correo: str = Field("", description="Correo electrónico")
    telefono: str = Field("", description="Teléfono, solo dígitos")
    rol: str = Field("", description="Rol inicial (nombre o identificador ROL-XX)")
    sede: str = Field("", description="Sede inicial (nombre o identificador SED-XX)")

    model_config = {"json_schema_extra": {"examples": [{
        "documento": "1098765432", "nombres": "Laura Patricia Rueda Gómez",
        "correo": "lrueda@empresa-transportadora.co", "telefono": "3157894512",
        "rol": "Coordinador de operaciones", "sede": "Bucaramanga",
    }]}}


class CambioEstadoEntrada(BaseModel):
    estado: str = Field("", description='Nuevo estado: "activo" o "inactivo"')
    motivo: str = Field("", description="Motivo del cambio")

    model_config = {"json_schema_extra": {"examples": [
        {"estado": "inactivo", "motivo": "Retiro voluntario de la empresa"}]}}


class TrasladoEntrada(BaseModel):
    sedeDestino: str = Field("", description="Sede de destino (nombre o identificador SED-XX)")

    model_config = {"json_schema_extra": {"examples": [{"sedeDestino": "Cúcuta"}]}}


class ContactoEntrada(BaseModel):
    correo: str | None = Field(None, description="Nuevo correo; si no se envía, no cambia")
    telefono: str | None = Field(None, description="Nuevo teléfono; si no se envía, no cambia")

    model_config = {"json_schema_extra": {"examples": [
        {"correo": "laura.rueda@empresa-transportadora.co", "telefono": "3157894512"}]}}
