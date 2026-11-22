"""Exploración real acotada mediante el mismo evaluador seguro de bisección."""
from .clasificacion_candidatos import clasificar_candidatos
from .contactos_eje import refinar_contactos
from ..base.contrato_exploracion import (
    EntradaExploracion, ResultadoExploracion, validar_exploracion,
)
from ..base.evaluacion_exploracion import muestrear_punto
from ...funcion_real.evaluacion.evaluador_funcion import compilar
from .muestreo_intervalos import generar_posiciones
from ...compartido.unidades_angulares import opciones_unidad


def explorar_intervalos(entrada: EntradaExploracion) -> ResultadoExploracion:
    """Devuelve candidatos y huecos; lanza ValueError por captura, sintaxis o presupuesto inválidos."""
    entrada = validar_exploracion(entrada)
    posiciones = generar_posiciones(entrada)
    funcion = compilar(entrada.expresion, **opciones_unidad(entrada.unidad_angular))
    muestras = tuple(muestrear_punto(funcion, posicion) for posicion in posiciones)
    candidatos = clasificar_candidatos(entrada.expresion, muestras, unidad_angular=entrada.unidad_angular)
    return refinar_contactos(entrada, muestras, candidatos, funcion)
