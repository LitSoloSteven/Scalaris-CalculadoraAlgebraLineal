"""Muestras reales controladas compartidas por malla y búsqueda local."""
from collections.abc import Callable

from .contrato_exploracion import MuestraExploracion
from .evaluador_funcion import evaluar


def muestrear_punto(funcion: Callable[[float], float], posicion: float) -> MuestraExploracion:
    """Devuelve valor finito o un fallo explícito de evaluación sin convertirlo en cero."""
    try:
        return MuestraExploracion(posicion, evaluar(funcion, posicion))
    except ValueError as error:
        return MuestraExploracion(posicion, None, str(error))
