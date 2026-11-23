from app.domain.exceptions.errores import DatosNoValidos, NoEncontrado, SolicitudIncorrecta
from app.repositories.adapters.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy
from app.services.contratos.ic11_consultar_sede import ids_de_sede, nombres_de_sedes
from app.services.contratos.ic20_consultar_rol_usuario import consultar_rol_usuario
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v

MENSAJE_503 = "No fue posible consultar los usuarios"


class ConsultarUsuarios:
    def __init__(self, db):
        self.db = db
        self.usuarios = UsuarioRepositorioSQLAlchemy(db)

    def ejecutar(self, documento=None, nombre=None, sede=None, estado=None) -> list[dict]:
        documento, nombre, sede = v.limpiar(documento), v.limpiar(nombre), v.limpiar(sede)
        estado = v.limpiar(estado).lower()
        if not any([documento, nombre, sede, estado]):
            raise SolicitudIncorrecta("Debe indicar al menos un criterio de búsqueda", [
                {"field": "criteria", "detail": "No se recibió document, name, site ni status"}])
        if estado and v.error_estado(estado):
            raise DatosNoValidos("Los criterios de búsqueda no son válidos", [v.error_estado(estado)])
        estado = api.estado_interno(estado) if estado else ""

        with transaccion(self.db, MENSAJE_503):
            id_sedes = ids_de_sede(self.db, sede) if sede else None
            encontrados = self.usuarios.buscar(documento or None, nombre or None, id_sedes, estado or None)
            if not encontrados:
                raise NoEncontrado("Sin resultados", [
                    {"field": "criteria", "detail": "No hay usuarios que cumplan todos los criterios"}])
            roles = consultar_rol_usuario(self.db, [u.documento for u in encontrados])
            sedes = nombres_de_sedes(self.db, [u.id_sede for u in encontrados])

        return [{"document": u.documento, "fullName": u.nombres, "role": roles.get(u.documento),
                 "site": sedes.get(u.id_sede), "status": api.estado(u.estado)} for u in encontrados]
