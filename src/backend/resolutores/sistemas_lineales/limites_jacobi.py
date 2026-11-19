"""Límites de captura y cálculo del método iterativo de Jacobi."""
from fractions import Fraction

MAXIMO_ITERACIONES_JACOBI = 100
MAXIMO_OPERACIONES_JACOBI = 50000
MAXIMO_BITS_ENTRADA_JACOBI = 4096
MAXIMO_BITS_CALCULO_JACOBI = 4096
MAXIMO_BITS_CAMBIO_JACOBI = 2 * MAXIMO_BITS_CALCULO_JACOBI + 2


def fraccion_admitida(valor: Fraction, maximo_bits: int) -> bool:
    """Indica si numerador y denominador caben en el límite de bits recibido."""
    return (
        abs(valor.numerator).bit_length() <= maximo_bits
        and valor.denominator.bit_length() <= maximo_bits
    )
