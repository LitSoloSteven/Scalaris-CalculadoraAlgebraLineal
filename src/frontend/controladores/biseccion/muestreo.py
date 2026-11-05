"""Muestreo acotado para dibujar funciones, sin certificar continuidad."""
import math
from statistics import median

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar
from src.backend.resolutores.raices.unidades_angulares import opciones_unidad

MUESTRAS_GRAFICA = 401
FACTOR_SALTO_SOSPECHOSO = 20


def muestrear_funcion(entrada: dict) -> dict:
    """Devuelve coordenadas y huecos; las evaluaciones inválidas nunca se unen."""
    funcion = compilar(entrada["expresion"], **opciones_unidad(entrada.get("unidad_angular", "radianes")))
    inferior, superior = entrada["extremo_izquierdo"], entrada["extremo_derecho"]
    abscisas = [inferior * (1 - indice / (MUESTRAS_GRAFICA - 1))
                + superior * (indice / (MUESTRAS_GRAFICA - 1)) for indice in range(MUESTRAS_GRAFICA)]
    ordenadas = [_evaluar_grafica(funcion, abscisa) for abscisa in abscisas]
    _interrumpir_restricciones(entrada, abscisas, ordenadas)
    _interrumpir_saltos(ordenadas)
    return {"x": abscisas, "y": ordenadas, "huecos": any(valor is None for valor in ordenadas)}


def separar_intervalo_sospechoso(muestra: dict, intervalo: tuple[float, float]) -> dict:
    """Corta segmentos que atraviesan el intervalo señalado por el motor sin evaluar puntos nuevos."""
    inferior, superior = intervalo
    abscisas = muestra["x"]
    ordenadas = list(muestra["y"])
    for indice, (izquierda, derecha) in enumerate(zip(abscisas, abscisas[1:]), 1):
        if izquierda < superior and derecha > inferior:
            ordenadas[indice] = None
    return {**muestra, "y": ordenadas, "huecos": any(valor is None for valor in ordenadas)}


def _interrumpir_restricciones(entrada: dict, abscisas: list, ordenadas: list) -> None:
    unidad = entrada.get("unidad_angular", "radianes")
    for indice in range(1, len(abscisas)):
        if ordenadas[indice - 1] is None or ordenadas[indice] is None:
            continue
        try:
            comprobar_dominio_intervalo(entrada["expresion"], (abscisas[indice - 1], abscisas[indice]),
                                        unidad_angular=unidad)
        except ValueError:
            ordenadas[indice] = None


def _interrumpir_saltos(ordenadas: list) -> None:
    magnitudes = [abs(valor) for valor in ordenadas if valor is not None]
    referencia = median(magnitudes) if magnitudes else 0
    originales = tuple(ordenadas)
    for indice in range(1, len(originales)):
        anterior, actual = originales[indice - 1:indice + 1]
        if anterior is None or actual is None:
            continue
        cambia_signo = math.copysign(1, anterior) != math.copysign(1, actual)
        if cambia_signo and min(abs(anterior), abs(actual)) > FACTOR_SALTO_SOSPECHOSO * referencia:
            ordenadas[indice] = None


def _evaluar_grafica(funcion, abscisa: float) -> float | None:
    try:
        valor = evaluar(funcion, abscisa)
        return valor if math.isfinite(valor) else None
    except (ValueError, TypeError, OverflowError, ZeroDivisionError, ErrorDominio, ErrorNoFinito):
        return None
