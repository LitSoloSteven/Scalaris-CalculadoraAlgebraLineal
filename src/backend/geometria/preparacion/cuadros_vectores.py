"""Suma exacta de pares de vectores y cuadros del escalamiento parametrizado."""
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class CuadroVectores:
    """Conserva el escalar y las coordenadas exactas de un cuadro vectorial."""

    escalar: Fraction
    vector_escalado: tuple[Fraction, ...]
    suma: tuple[Fraction, ...]


def calcular_suma_vectores(
    primer_vector: list[Fraction], segundo_vector: list[Fraction],
) -> list[Fraction]:
    """Devuelve la suma exacta de dos vectores Fraction ya validados de igual dimensión sin mutarlos."""
    return [primero + segundo for primero, segundo in zip(primer_vector, segundo_vector)]


def calcular_cuadros_vectores(
    primer_vector: list[Fraction], segundo_vector: list[Fraction],
) -> list[CuadroVectores]:
    """Devuelve 25 cuadros exactos de k·u + v para dos listas Fraction de igual dimensión ya validadas.
    Los cuadros se ordenan por escalar entre -3 y 3, incluidos, en pasos de 1/4."""
    cuadros = []
    for indice in range(-12, 13):
        escalar = Fraction(indice, 4)
        escalado = [escalar * componente for componente in primer_vector]
        suma = calcular_suma_vectores(escalado, segundo_vector)
        cuadros.append(CuadroVectores(escalar, tuple(escalado), tuple(suma)))
    return cuadros
