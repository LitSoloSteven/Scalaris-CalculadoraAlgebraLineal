"""Representación decimal exacta de los racionales admitidos por los métodos iterativos."""
from decimal import Decimal
from fractions import Fraction


def formatear_racional_exacto(valor: Fraction) -> str:
    """Devuelve numerador y denominador completos sin cambiar el límite global de enteros."""
    numerador = format(Decimal(valor.numerator), "f")
    if valor.denominator == 1:
        return numerador
    denominador = format(Decimal(valor.denominator), "f")
    return f"{numerador}/{denominador}"
