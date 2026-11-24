class ErrorNegocio(Exception):
    codigo = 400

    def __init__(self, mensaje: str, errores: list[dict] | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.errores = errores or []


class SolicitudIncorrecta(ErrorNegocio):
    codigo = 400


class SesionNoValida(ErrorNegocio):
    codigo = 401


class PermisoDenegado(ErrorNegocio):
    codigo = 403


class NoEncontrado(ErrorNegocio):
    codigo = 404


class Conflicto(ErrorNegocio):
    codigo = 409


class DatosNoValidos(ErrorNegocio):
    codigo = 422


class ServicioNoDisponible(ErrorNegocio):
    codigo = 503
