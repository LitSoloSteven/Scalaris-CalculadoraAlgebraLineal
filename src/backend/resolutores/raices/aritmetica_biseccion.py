"""Aritmética acotada del intervalo y las métricas de bisección."""
import math

from .errores_numericos import ErrorCapacidadNumerica


def ancho_intervalo(inferior: float, superior: float) -> float:
    """Devuelve el ancho finito; lanza ErrorNoFinito si no puede representarse."""
    ancho = superior - inferior
    if not math.isfinite(ancho):
        raise ErrorCapacidadNumerica("El ancho del intervalo excede la capacidad numérica. Reduce sus extremos.", "ANCHO_NO_REPRESENTABLE")
    return ancho


def punto_medio(inferior: float, superior: float) -> float:
    """Obtiene el punto medio evitando sumar extremos grandes del mismo signo."""
    if (inferior < 0) != (superior < 0):
        return inferior / 2 + superior / 2
    return inferior + (superior - inferior) / 2


def cota_intervalo(inferior: float, superior: float) -> float:
    """Devuelve el semiancho finito o informa una pérdida de representación."""
    ancho = ancho_intervalo(inferior, superior)
    cota = ancho / 2
    if ancho > 0 and cota == 0:
        raise ErrorCapacidadNumerica("La cota geométrica no puede representarse sin redondearla a cero.", "SUBDESBORDAMIENTO")
    return cota


def error_relativo_numerico(actual: float, previo: float | None) -> float | None:
    """Devuelve el porcentaje sin redondear o None si es indefinido o no representable."""
    if previo is None or actual == 0:
        return None
    valor = abs((actual - previo) / actual) * 100
    return valor if math.isfinite(valor) else None
