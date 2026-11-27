from typing import Protocol


class ServicioDistancias(Protocol):
    def distancia_estimada_km(self, origen: str, destino: str) -> float | None:
        ...
