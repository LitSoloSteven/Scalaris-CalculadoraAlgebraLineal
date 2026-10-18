"""Conversión de coordenadas exactas para su representación gráfica."""
from fractions import Fraction


def a_flotante_seguro(valor: Fraction) -> float | None:
    """Convierte una fracción a flotante; devuelve None si no se puede representar."""
    try:
        return float(valor)
    except (OverflowError, ValueError):
        return None
