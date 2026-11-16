"""Caso de uso FUN-11 / PRO-11: crear un rol o reemplazar su conjunto de permisos."""

from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.rol import Rol
from app.domain.exceptions.errores import ServicioNoDisponible
from app.domain.interfaces.rol_repositorio import RolRepositorio
from app.services.validators import rol_validador


@dataclass
class ResultadoConfiguracion:
    rol: Rol
    accion: str  # "creado" o "actualizado"


class ConfigurarRol:
    def __init__(self, repositorio: RolRepositorio):
        self.repositorio = repositorio

    def ejecutar(self, nombre: str, descripcion: str, permisos: list[str], responsable: str) -> ResultadoConfiguracion:
        nombre = nombre.strip()
        permisos = rol_validador.normalizar_permisos(permisos)
        rol_validador.validar_datos_basicos(nombre, permisos)

        try:
            existentes = self.repositorio.operaciones_existentes(permisos)
            rol_validador.validar_operaciones(permisos, existentes)

            actual = self.repositorio.buscar_por_nombre(nombre)
            if actual is None:
                rol = Rol(id_rol=self.repositorio.siguiente_id(), nombre=nombre,
                          descripcion=descripcion.strip(), estado="activo", permisos=permisos)
                accion = "creado"
            else:
                rol = Rol(id_rol=actual.id_rol, nombre=actual.nombre,
                          descripcion=descripcion.strip() or actual.descripcion,
                          estado=actual.estado, permisos=permisos)
                accion = "actualizado"

            guardado = self.repositorio.guardar(rol, responsable)
        except SQLAlchemyError as exc:
            raise ServicioNoDisponible(
                "No fue posible guardar la configuración del rol",
                [{"campo": "baseDeDatos", "detalle": "La base de datos no está disponible"}],
            ) from exc

        guardado.permisos = permisos
        return ResultadoConfiguracion(rol=guardado, accion=accion)
