"""Conversión numérica exacta antes de obtener valores aproximados de presentación."""
from fractions import Fraction
from typing import Any


def a_flotante(valor: Any) -> float:
    """Convierte un valor numérico a flotante; lanza ValueError si no es convertible."""
    try:
        return float(Fraction(str(valor).strip()))
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(f"Valor no numérico: {valor!r}") from error
