from pydantic import BaseModel, Field


class RegistroUsuarioEntrada(BaseModel):
    document: str = Field("", description="Documento de identidad, solo dígitos")
    fullName: str = Field("", description="Nombres y apellidos")
    email: str = Field("", description="Correo electrónico")
    phone: str = Field("", description="Teléfono, solo dígitos")
    role: str = Field("", description="Rol inicial (nombre o identificador ROL-XX)")
    site: str = Field("", description="Sede inicial (nombre o identificador SED-XX)")

    model_config = {"json_schema_extra": {"examples": [{
        "document": "1098765432", "fullName": "Laura Patricia Rueda Gómez",
        "email": "lrueda@empresa-transportadora.co", "phone": "3157894512",
        "role": "Coordinador de operaciones", "site": "Bucaramanga",
    }]}}


class CambioEstadoEntrada(BaseModel):
    status: str = Field("", description='Nuevo estado: "active" o "inactive"')
    reason: str = Field("", description="Motivo del cambio")

    model_config = {"json_schema_extra": {"examples": [
        {"status": "inactive", "reason": "Retiro voluntario de la empresa"}]}}


class TrasladoEntrada(BaseModel):
    destinationSite: str = Field("", description="Sede de destino (nombre o identificador SED-XX)")

    model_config = {"json_schema_extra": {"examples": [{"destinationSite": "Cúcuta"}]}}


class ContactoEntrada(BaseModel):
    email: str | None = Field(None, description="Nuevo correo; si no se envía, no cambia")
    phone: str | None = Field(None, description="Nuevo teléfono; si no se envía, no cambia")

    model_config = {"json_schema_extra": {"examples": [
        {"email": "laura.rueda@empresa-transportadora.co", "phone": "3157894512"}]}}
