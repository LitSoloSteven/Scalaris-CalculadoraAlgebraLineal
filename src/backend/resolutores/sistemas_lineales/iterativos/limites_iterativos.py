"""Límites de captura y cálculo compartidos por los métodos iterativos."""
from fractions import Fraction

from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS

MAXIMO_ITERACIONES_ITERATIVO = 100
# Para orden n, el residuo inicial cuesta n(2n + 1) cargos y cada barrido con su residuo n(4n + 1).
# Los topes vigentes permiten hasta 41 210 cargos. El límite conserva un margen.
MAXIMO_OPERACIONES_ITERATIVO = 50000
MAXIMO_BITS_ENTRADA_ITERATIVO = 4096
MAXIMO_BITS_CALCULO_ITERATIVO = 4096
_MAXIMO_BITS_VECTOR_ITERATIVO = max(
    MAXIMO_BITS_ENTRADA_ITERATIVO, MAXIMO_BITS_CALCULO_ITERATIVO,
)
# La norma del cambio en la traza tiene una cota propia de bits y queda fuera del contador.
MAXIMO_BITS_CAMBIO_ITERATIVO = 2 * _MAXIMO_BITS_VECTOR_ITERATIVO + 2
# Cada término aporta los bits de un producto y la suma añade el margen del número de términos.
MAXIMO_BITS_ACUMULACION_ITERATIVO = (
    (MAXIMO_BITS_ENTRADA_ITERATIVO + _MAXIMO_BITS_VECTOR_ITERATIVO)
    * DIMENSION_MAXIMA_SISTEMAS + (DIMENSION_MAXIMA_SISTEMAS - 1).bit_length()
)


def fraccion_admitida(valor: Fraction, maximo_bits: int) -> bool:
    """Indica si numerador y denominador caben en el límite de bits recibido."""
    return (
        abs(valor.numerator).bit_length() <= maximo_bits
        and valor.denominator.bit_length() <= maximo_bits
    )
