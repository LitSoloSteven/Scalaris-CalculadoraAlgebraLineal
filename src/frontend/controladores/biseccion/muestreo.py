"""Muestreo acotado para dibujar funciones, sin certificar continuidad."""
import math

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar

MUESTRAS_GRAFICA = 401


def muestrear_funcion(entrada: dict) -> dict:
    """Devuelve coordenadas y huecos; las evaluaciones inválidas nunca se unen."""
    funcion = compilar(entrada["expresion"])
    inferior, superior = entrada["extremo_izquierdo"], entrada["extremo_derecho"]
    abscisas = [inferior * (1 - indice / (MUESTRAS_GRAFICA - 1))
                + superior * (indice / (MUESTRAS_GRAFICA - 1)) for indice in range(MUESTRAS_GRAFICA)]
    ordenadas = [_evaluar_grafica(funcion, abscisa) for abscisa in abscisas]
    # Un salto con cambio de signo y crecimiento local fuerte puede ocultar un polo entre muestras.
    for indice in range(1, len(ordenadas) - 1):
        anterior, actual, siguiente = ordenadas[indice - 1:indice + 2]
        if None not in (anterior, actual, siguiente) and anterior * actual < 0:
            if abs(actual - anterior) > 8 * max(abs(siguiente - actual), 1e-300):
                ordenadas[indice] = None
    return {"x": abscisas, "y": ordenadas, "huecos": any(valor is None for valor in ordenadas)}


def _evaluar_grafica(funcion, abscisa: float) -> float | None:
    try:
        valor = evaluar(funcion, abscisa)
        return valor if math.isfinite(valor) else None
    except (ValueError, TypeError, OverflowError, ZeroDivisionError, ErrorDominio, ErrorNoFinito):
        return None
