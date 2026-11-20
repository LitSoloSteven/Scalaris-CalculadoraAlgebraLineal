"""Conversión exacta de racionales para operaciones de filas y serialización."""
from decimal import Decimal
from fractions import Fraction


def convertir_fraccion(valor: int | float | Fraction) -> Fraction:
    """Devuelve una Fraction exacta; conserva errores de Fraction para valores no convertibles."""
    return valor if type(valor) is Fraction else Fraction(valor)


def convertir_fila_fracciones(fila: list[int | float | Fraction]) -> list[Fraction]:
    """Convierte una fila sin modificarla; reutiliza solo Fraction de tipo exacto e inmutable."""
    return [convertir_fraccion(valor) for valor in fila]


def texto_entero_exacto(valor: int) -> str:
    """Convierte un entero a texto aunque supere el límite de dígitos de CPython."""
    try:
        return str(valor)
    except ValueError:
        return format(Decimal(valor), "f")


def texto_fraccion_exacta(valor: int | Fraction) -> str:
    """Devuelve la fracción como texto exacto, con el mismo formato que el codificador común."""
    fraccion = Fraction(valor)
    if fraccion.denominator == 1:
        return texto_entero_exacto(fraccion.numerator)
    return (
        f"{texto_entero_exacto(fraccion.numerator)}/"
        f"{texto_entero_exacto(fraccion.denominator)}"
    )
