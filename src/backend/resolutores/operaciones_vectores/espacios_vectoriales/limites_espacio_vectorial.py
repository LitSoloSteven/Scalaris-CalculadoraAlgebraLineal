"""Topes de entrada y de expansión para el análisis polinómico."""
from fractions import Fraction

MAXIMO_GRADO_ENTRADA = 8
MAXIMO_TERMINOS_ENTRADA = 128
MAXIMO_BITS_ENTRADA = 1024
MAXIMO_GRADO_CALCULO = MAXIMO_GRADO_ENTRADA ** 2
MAXIMO_TERMINOS_CALCULO = 2048
MAXIMO_BITS_CALCULO = 4096
MAXIMO_OPERACIONES = 150_000


class LimiteAritmeticoEspacio(ArithmeticError):
    """Indica que una expansión exacta superó una cota de cálculo."""


def racional_admitido(valor: Fraction | int, maximo_bits: int) -> bool:
    """Indica si el numerador y el denominador caben en la cota indicada."""
    return max(valor.numerator.bit_length(), valor.denominator.bit_length()) <= maximo_bits
