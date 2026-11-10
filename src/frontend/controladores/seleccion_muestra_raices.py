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
    if not _identifica_muestra(punto, len(muestra["x"]), identidad):
        return None
    indice = punto["pointIndex"]
    abscisa, ordenada = muestra["x"][indice], muestra["y"][indice]
    if not _numero_finito(ordenada) or not _numero_finito(punto.get("x")):
        return None
    if not _numero_finito(punto.get("y")):
        return None
    return abscisa if punto["x"] == abscisa and punto["y"] == ordenada else None


def _identifica_muestra(punto: dict, cantidad: int, identidad: str) -> bool:
    traza, indice = punto.get("curveNumber"), punto.get("pointIndex")
    return (type(traza) is int and traza == 0 and type(indice) is int
            and 0 <= indice < cantidad and punto.get("customdata") == identidad)


def _numero_finito(valor: object) -> bool:
    if type(valor) not in (int, float):
        return False
    try:
        return isfinite(valor)
    except OverflowError:
        return False
