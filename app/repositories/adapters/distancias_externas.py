import logging

log = logging.getLogger("huella.distancias")


class DistanciasSinProveedor:

    def distancia_estimada_km(self, origen: str, destino: str) -> float | None:
        log.info("API-EXT-01 sin proveedor configurado: %s -> %s se programa sin distancia estimada", origen, destino)
        return None


def obtener_servicio_distancias():
    return DistanciasSinProveedor()
