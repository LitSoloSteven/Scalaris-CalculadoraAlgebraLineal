"""Unidad angular explícita para trigonometría real y contratos compatibles."""
import math

from .errores_numericos import ErrorCapacidadNumerica

UNIDAD_ANGULAR_DEFECTO = "radianes"
UNIDADES_ANGULARES = (UNIDAD_ANGULAR_DEFECTO, "grados")
_DIRECTAS = frozenset(("sin", "cos", "tan"))
_INVERSAS = frozenset(("asin", "acos", "atan"))


def funcion_sensible_a_unidad(nombre: str) -> bool:
    """Indica si la llamada usa la unidad angular; lanza ValueError si el nombre no es texto."""
    if not isinstance(nombre, str):
        raise ValueError("El nombre de la función debe ser texto.")
    return nombre in _DIRECTAS or nombre in _INVERSAS


def validar_unidad_angular(unidad: str) -> str:
    """Devuelve la unidad canónica; lanza ValueError si no es radianes o grados."""
    if not isinstance(unidad, str) or unidad not in UNIDADES_ANGULARES:
        raise ValueError("La unidad angular debe ser radianes o grados.")
    return unidad


def opciones_unidad(unidad: str) -> dict[str, str]:
    """Entrega la opción no predeterminada validada para consumidores compatibles; lanza ValueError."""
    unidad = validar_unidad_angular(unidad)
    return {} if unidad == UNIDAD_ANGULAR_DEFECTO else {"unidad_angular": unidad}


def argumento_angular(nombre: str, argumento: float, unidad: str) -> float:
    """Convierte entradas trigonométricas a radianes; rechaza pérdida total de un ángulo no nulo."""
    if unidad != "grados" or nombre not in _DIRECTAS:
        return argumento
    convertido = math.radians(argumento)
    if argumento != 0 and convertido == 0:
        raise ErrorCapacidadNumerica("El ángulo se redondea a cero al convertirlo a radianes.", "SUBDESBORDAMIENTO")
    return convertido


def resultado_angular(nombre: str, resultado: float, unidad: str) -> float:
    """Convierte únicamente salidas trigonométricas inversas a la unidad solicitada."""
    return math.degrees(resultado) if unidad == "grados" and nombre in _INVERSAS else resultado
