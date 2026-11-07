"""Aritmetica acotada del peso escalado y la aproximacion de regla falsa."""
import math

from .aritmetica_biseccion import ancho_intervalo, error_relativo_numerico
from .errores_numericos import ErrorCapacidadNumerica


def peso_escalado(valor_inferior: float, valor_superior: float) -> float:
    """Devuelve f(a) / (f(a) - f(b)); rechaza denominador nulo o resultado no finito."""
    if valor_inferior == valor_superior:
        raise ErrorCapacidadNumerica(
            "El denominador de la secante es nulo; no es posible aproximar.",
            "ANCHO_NO_REPRESENTABLE",
        )
    try:
        peso = valor_inferior / (valor_inferior - valor_superior)
    except ZeroDivisionError as error:
        raise ErrorCapacidadNumerica(
            "El denominador de la secante es nulo; no es posible aproximar.",
            "ANCHO_NO_REPRESENTABLE",
        ) from error
    if not math.isfinite(peso):
        raise ErrorCapacidadNumerica(
            "El peso de la secante excede la capacidad numerica.",
            "ANCHO_NO_REPRESENTABLE",
        )
    return peso


def punto_cruce(
    inferior: float, superior: float, valor_inferior: float, valor_superior: float
) -> float:
    """Devuelve c = a + w*(b-a) sin desbordar la suma."""
    ancho = ancho_intervalo(inferior, superior)
    peso = peso_escalado(valor_inferior, valor_superior)
    contribucion = ancho * peso
    if not math.isfinite(contribucion):
        raise ErrorCapacidadNumerica(
            "La aproximacion de la secante excede la capacidad numerica.",
            "ANCHO_NO_REPRESENTABLE",
        )
    cruce = inferior + contribucion
    if not math.isfinite(cruce):
        raise ErrorCapacidadNumerica(
            "La aproximacion de la secante excede la capacidad numerica.",
            "ANCHO_NO_REPRESENTABLE",
        )
    return cruce