"""Límites de captura y cálculo del método iterativo de Jacobi."""
from fractions import Fraction

from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS

MAXIMO_ITERACIONES_JACOBI = 100
MAXIMO_OPERACIONES_JACOBI = 50000
MAXIMO_BITS_ENTRADA_JACOBI = 4096
MAXIMO_BITS_CALCULO_JACOBI = 4096
_MAXIMO_BITS_VECTOR_JACOBI = max(MAXIMO_BITS_ENTRADA_JACOBI, MAXIMO_BITS_CALCULO_JACOBI)
MAXIMO_BITS_CAMBIO_JACOBI = 2 * _MAXIMO_BITS_VECTOR_JACOBI + 2
# Cada término aporta los bits de un producto y la suma añade el margen del número de términos.
MAXIMO_BITS_ACUMULACION_JACOBI = (
    (MAXIMO_BITS_ENTRADA_JACOBI + _MAXIMO_BITS_VECTOR_JACOBI)
    * DIMENSION_MAXIMA_SISTEMAS + (DIMENSION_MAXIMA_SISTEMAS - 1).bit_length()
)


def fraccion_admitida(valor: Fraction, maximo_bits: int) -> bool:
    """Indica si numerador y denominador caben en el límite de bits recibido."""
    return (
        abs(valor.numerator).bit_length() <= maximo_bits
        and valor.denominator.bit_length() <= maximo_bits
    )
