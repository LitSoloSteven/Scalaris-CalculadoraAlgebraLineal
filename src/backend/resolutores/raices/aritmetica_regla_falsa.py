"""Aritmetica acotada del peso escalado y la aproximacion de regla falsa."""
import math

from .aritmetica_biseccion import ancho_intervalo, error_relativo_numerico  # noqa: F401  reexport para traza_regla_falsa
from .errores_numericos import ErrorCapacidadNumerica


def peso_escalado(valor_inferior: float, valor_superior: float) -> float:
    """Devuelve t normalizado; lanza ErrorCapacidadNumerica si los valores son iguales o no finitos."""
    if valor_inferior == valor_superior:
        raise ErrorCapacidadNumerica(
            "El denominador de la secante es nulo; no es posible aproximar.",
            "INTERPOLACION_NO_REPRESENTABLE",
        )
    escala = max(abs(valor_inferior), abs(valor_superior))
    if not math.isfinite(escala):
        raise ErrorCapacidadNumerica(
            "No es posible interpolar con estos valores.",
            "INTERPOLACION_NO_REPRESENTABLE",
        )
    relativo_inferior = abs(valor_inferior) / escala
    relativo_superior = abs(valor_superior) / escala
    return relativo_inferior / (relativo_inferior + relativo_superior)


def punto_cruce(
    inferior: float, superior: float, valor_inferior: float, valor_superior: float
) -> float:
    """Devuelve c acotado a [a, b]; lanza ErrorCapacidadNumerica si el ancho no es representable."""
    ancho_intervalo(inferior, superior)
    peso = peso_escalado(valor_inferior, valor_superior)
    cruce = (1.0 - peso) * inferior + peso * superior
    if not math.isfinite(cruce):
        raise ErrorCapacidadNumerica(
            "La aproximacion de la secante excede la capacidad numerica.",
            "ANCHO_NO_REPRESENTABLE",
        )
    return min(max(cruce, inferior), superior)