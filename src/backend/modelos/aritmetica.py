"""Comparaciones exactas de dominio y tolerancia para entradas aproximadas."""
from fractions import Fraction
from math import isfinite

from src.backend.constantes import CERO_EPSILON


def es_cero(valor: int | Fraction | float, tolerancia: float = CERO_EPSILON) -> bool:
    """Devuelve si valor es cero; aplica tolerancia solamente a flotantes."""
    if isinstance(valor, (int, Fraction)):
        return valor == 0
    return valor == 0 or abs(valor) < tolerancia


def numeros_iguales(izquierda: int | Fraction | float, derecha: int | Fraction | float) -> bool:
    """Compara racionales exactamente y flotantes finitos con la tolerancia del dominio."""
    if isinstance(izquierda, (int, Fraction)) and isinstance(derecha, (int, Fraction)):
        return izquierda == derecha
    if any(isinstance(valor, float) and not isfinite(valor) for valor in (izquierda, derecha)):
        return False
    return abs(Fraction(izquierda) - Fraction(derecha)) < Fraction(CERO_EPSILON)
