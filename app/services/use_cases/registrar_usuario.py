from app.domain.entities.usuario import Usuario
from app.domain.exceptions.errores import Conflicto, DatosNoValidos
from app.domain.interfaces.servicio_correo import ServicioCorreo
from app.domain.value_objects.fecha import ahora
from app.repositories.adapters.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy
from app.services.contratos.ic11_consultar_sede import consultar_sede, error_de_sede
from app.services.contratos.ic12_registrar_credenciales_y_rol import consultar_rol, registrar_credenciales_y_rol
from app.services.mappers import api
from app.services.use_cases.transaccion import transaccion
from app.services.validators import usuario_validador as v

MENSAJE_503 = "No fue posible registrar el usuario. Intente nuevamente más tarde"
DUPLICADO = "Ya existe un usuario con el documento o el correo indicado"


class RegistrarUsuario:
    def __init__(self, db, correo: ServicioCorreo):
        self.db = db
        self.usuarios = UsuarioRepositorioSQLAlchemy(db)
        self.correo = correo

    def ejecutar(self, documento, nombres, correo, telefono, rol, sede, responsable: str) -> tuple[dict, bool]:
        datos = {
            "documento": "".join((documento or "").split()),
            "nombres": v.limpiar(nombres),
            "correo": v.limpiar(correo).lower(),
            "telefono": "".join((telefono or "").split()),
            "rol": v.limpiar(rol),
            "sede": v.limpiar(sede),
        }
        v.validar_registro(datos)

        conflicto = Conflicto(DUPLICADO, [{"field": "document", "detail": "El documento o el correo ya está registrado"}])
        with transaccion(self.db, MENSAJE_503, conflicto):
            repetidos = []
            if self.usuarios.buscar_por_documento(datos["documento"]):
                repetidos.append({"field": "document", "detail": f"El documento {datos['documento']} ya está registrado"})
            if self.usuarios.buscar_por_correo(datos["correo"]):
                repetidos.append({"field": "email", "detail": f"El correo {datos['correo']} ya está registrado"})
            if repetidos:
                raise Conflicto(DUPLICADO, repetidos)

            sede = consultar_sede(self.db, datos["sede"])
            rol = consultar_rol(self.db, datos["rol"])
            no_disponibles = [e for e in [error_de_sede(sede, datos["sede"], "site")] if e]
            if rol is None:
                no_disponibles.append({"field": "role", "detail": f"El rol {datos['rol']} no existe"})
            elif rol.estado != "activo":
                no_disponibles.append({"field": "role", "detail": f"El rol {rol.nombre} se encuentra inactivo"})
            if no_disponibles:
                raise DatosNoValidos("La sede o el rol indicados no están disponibles", no_disponibles)

            usuario = Usuario(id_usuario=self.usuarios.siguiente_id(), documento=datos["documento"],
                              nombres=datos["nombres"], correo=datos["correo"], telefono=datos["telefono"],
                              id_sede=sede["idSede"], estado="activo", fecha_creacion=ahora())
            self.usuarios.agregar(usuario, responsable)
            temporal = registrar_credenciales_y_rol(self.db, usuario.documento, rol.id_rol)
            self.db.commit()

        enviadas = self.correo.enviar(
            usuario.correo,
            "Credenciales de acceso - Huella de Carbono",
            f"Hola {usuario.nombres}:\n\n"
            f"Se creó su usuario en el sistema de seguimiento de combustible y emisiones de CO₂.\n"
            f"Usuario: {usuario.documento} (o su correo {usuario.correo})\n"
            f"Contraseña temporal: {temporal}\n\n"
            f"Al ingresar por primera vez el sistema le pedirá cambiarla.",
        )
        respuesta = {
            "userId": usuario.id_usuario, "document": usuario.documento, "fullName": usuario.nombres,
            "email": usuario.correo, "role": rol.nombre, "site": sede["nombre"], "status": api.estado(usuario.estado),
            "credentialsSent": enviadas,
        }
        return respuesta, enviadas
