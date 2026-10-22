"""Conversión exacta para operaciones de filas sin reconstruir racionales canónicos."""
from fractions import Fraction


def convertir_fraccion(valor: int | float | Fraction) -> Fraction:
    """Devuelve una Fraction exacta; conserva errores de Fraction para valores no convertibles."""
    return valor if type(valor) is Fraction else Fraction(valor)


def convertir_fila_fracciones(fila: list[int | float | Fraction]) -> list[Fraction]:
    """Convierte una fila sin modificarla; reutiliza solo Fraction de tipo exacto e inmutable."""
    return [convertir_fraccion(valor) for valor in fila]
