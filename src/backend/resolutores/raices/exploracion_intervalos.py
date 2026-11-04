"""Exploración real acotada mediante el mismo evaluador seguro de bisección."""
from collections.abc import Callable

from .clasificacion_candidatos import clasificar_candidatos
from .contrato_exploracion import (
    EntradaExploracion, MuestraExploracion, ResultadoExploracion, validar_exploracion,
)
from .evaluador_funcion import compilar, evaluar
from .muestreo_intervalos import generar_posiciones


def explorar_intervalos(entrada: EntradaExploracion) -> ResultadoExploracion:
    """Devuelve candidatos y huecos; lanza ValueError por captura, sintaxis o presupuesto inválidos."""
    entrada = validar_exploracion(entrada)
    posiciones = generar_posiciones(entrada)
    funcion = compilar(entrada.expresion)
    muestras = tuple(_muestrear(funcion, posicion) for posicion in posiciones)
    candidatos = clasificar_candidatos(entrada.expresion, muestras)
    return ResultadoExploracion(candidatos, len(muestras))


def _muestrear(funcion: Callable[[float], float], posicion: float) -> MuestraExploracion:
    try:
        return MuestraExploracion(posicion, evaluar(funcion, posicion))
    except ValueError as error:
        return MuestraExploracion(posicion, None, str(error))
