"""Búsqueda local de menor magnitud sin ejecutar bisección ni certificar multiplicidad."""
from collections.abc import Callable
from dataclasses import replace

from .aritmetica_biseccion import punto_medio
from .clasificacion_candidatos import AVISO_CONTACTO, clasificar_candidatos
from .contrato_exploracion import CandidatoExploracion, EntradaExploracion, EvidenciaContacto, MuestraExploracion
from .evaluacion_exploracion import muestrear_punto
from .limites_exploracion import (
    EVALUACIONES_POR_REFINAMIENTO, MAXIMO_EVALUACIONES_REFINAMIENTO, MAXIMO_REFINAMIENTOS_CONTACTO,
)


def refinar_contacto(entrada: EntradaExploracion, funcion: Callable[[float], float],
                     muestras: tuple[MuestraExploracion, ...], presupuesto: int) -> tuple[CandidatoExploracion, ...]:
    """Refina tres muestras válidas y devuelve sus hallazgos; presupuesto inválido lanza ValueError."""
    if type(presupuesto) is not int or not 0 <= presupuesto <= MAXIMO_EVALUACIONES_REFINAMIENTO:
        raise ValueError("El presupuesto auxiliar debe ser un entero dentro del límite global.")
    vecinos = muestras
    evaluaciones = refinamientos = 0
    motivo = "limite_refinamientos"
    hallazgos = ()
    for _ in range(MAXIMO_REFINAMIENTOS_CONTACTO):
        if presupuesto - evaluaciones < EVALUACIONES_POR_REFINAMIENTO:
            motivo = "presupuesto_global"
            break
        sondeos = _sondear(funcion, vecinos)
        if sondeos is None:
            motivo = "precision"
            break
        evaluaciones += EVALUACIONES_POR_REFINAMIENTO
        refinamientos += 1
        ampliadas = (vecinos[0], sondeos[0], vecinos[1], sondeos[1], vecinos[2])
        hallazgos = _hallazgos(entrada, ampliadas)
        if hallazgos:
            motivo = hallazgos[0].tipo
            break
        indice = min(range(1, 4), key=lambda indice: abs(ampliadas[indice].valor))
        vecinos = ampliadas[indice - 1:indice + 2]
    if not hallazgos:
        hallazgos = (CandidatoExploracion("posible_contacto", (vecinos[0].abscisa, vecinos[2].abscisa),
                                          vecinos[1].abscisa, vecinos[1].valor, AVISO_CONTACTO),)
    evidencia = EvidenciaContacto(muestras[1].valor, min(abs(muestras[0].valor), abs(muestras[2].valor)),
                                 evaluaciones, refinamientos, motivo)
    return (replace(hallazgos[0], evidencia_contacto=evidencia), *hallazgos[1:])


def _sondear(funcion: Callable[[float], float], vecinos: tuple) -> tuple | None:
    izquierda, centro, derecha = vecinos
    inferior = punto_medio(izquierda.abscisa, centro.abscisa)
    superior = punto_medio(centro.abscisa, derecha.abscisa)
    if not izquierda.abscisa < inferior < centro.abscisa < superior < derecha.abscisa:
        return None
    return muestrear_punto(funcion, inferior), muestrear_punto(funcion, superior)


def _hallazgos(entrada: EntradaExploracion, muestras: tuple) -> tuple[CandidatoExploracion, ...]:
    registros = clasificar_candidatos(entrada.expresion, muestras, unidad_angular=entrada.unidad_angular)
    tipos = ("segmento_invalido", "discontinuidad", "cero_evaluado", "cruce")
    return tuple(registro for tipo in tipos for registro in registros if registro.tipo == tipo)
