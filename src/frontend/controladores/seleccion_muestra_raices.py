"""Validación de eventos nativos contra la curva vigente del servidor."""
from math import isfinite


def abscisa_muestreada(datos: object, muestra: dict, identidad: str) -> float | None:
    """Devuelve la abscisa de un solo punto auténtico o descarta el evento."""
    if not isinstance(datos, dict):
        return None
    puntos = datos.get("points")
    if not isinstance(puntos, list) or len(puntos) != 1 or not isinstance(puntos[0], dict):
        return None
    punto = puntos[0]
    indice = punto.get("pointIndex")
    if type(punto.get("curveNumber")) is not int or punto["curveNumber"] != 0:
        return None
    if type(indice) is not int or not 0 <= indice < len(muestra["x"]):
        return None
    if punto.get("customdata") != identidad:
        return None
    abscisa, ordenada = muestra["x"][indice], muestra["y"][indice]
    if not _numero_finito(ordenada) or not _numero_finito(punto.get("x")):
        return None
    if not _numero_finito(punto.get("y")):
        return None
    return abscisa if punto["x"] == abscisa and punto["y"] == ordenada else None


def _numero_finito(valor: object) -> bool:
    if type(valor) not in (int, float):
        return False
    try:
        return isfinite(valor)
    except OverflowError:
        return False
