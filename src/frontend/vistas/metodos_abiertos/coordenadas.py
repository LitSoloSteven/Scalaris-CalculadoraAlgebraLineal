"""Conversión segura de coordenadas usadas en la gráfica."""
import math


def numero_finito(valor) -> float | None:
    """Devuelve un valor numérico finito o `None` cuando no puede graficarse."""
    try:
        numero = float(valor)
    except (TypeError, ValueError, OverflowError):
        return None
    return numero if math.isfinite(numero) else None
