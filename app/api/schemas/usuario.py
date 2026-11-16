"""Esquemas de entrada del módulo MOD-01 Gestión de Usuarios.

Los campos llegan como texto opcional: que estén completos y con formato válido lo
valida cada caso de uso, para responder con el mensaje de cada campo que pide la historia.
"""

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
