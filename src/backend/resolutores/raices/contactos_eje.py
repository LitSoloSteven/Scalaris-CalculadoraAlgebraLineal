"""Refinamiento de semillas locales con consumo global y registros conservados."""
from collections.abc import Callable

from .contrato_exploracion import (
    AVISO_EXPLORACION, CandidatoExploracion, EntradaExploracion, MuestraExploracion, ResultadoExploracion,
)
from .limites_exploracion import MAXIMO_EVALUACIONES_REFINAMIENTO, MAXIMO_REGISTROS_EXPLORACION
from .refinamiento_contactos import refinar_contacto

AVISO_REFINAMIENTO_AGOTADO = (
    "Se agotó el presupuesto auxiliar de contactos. Se conservan los candidatos pendientes "
    "sin certificar raíces; reduce el rango o el paso para inspeccionarlos de nuevo."
)


def refinar_contactos(entrada: EntradaExploracion, muestras: tuple[MuestraExploracion, ...],
                      candidatos: tuple[CandidatoExploracion, ...], funcion: Callable[[float], float]) -> ResultadoExploracion:
    """Refina semillas de la malla validada en orden estable sin añadir evaluaciones fuera del presupuesto."""
    indices = {muestra.abscisa: indice for indice, muestra in enumerate(muestras)}
    registros = []
    evaluaciones = refinamientos = 0
    agotado = False
    for candidato in candidatos:
        nuevos = (candidato,)
        if candidato.tipo == "posible_contacto":
            indice = indices[candidato.abscisa]
            presupuesto = MAXIMO_EVALUACIONES_REFINAMIENTO - evaluaciones
            nuevos = refinar_contacto(entrada, funcion, muestras[indice - 1:indice + 2], presupuesto)
            evidencia = nuevos[0].evidencia_contacto
            evaluaciones += evidencia.evaluaciones
            refinamientos += evidencia.refinamientos
            agotado |= evidencia.motivo == "presupuesto_global"
        if len(registros) + len(nuevos) > MAXIMO_REGISTROS_EXPLORACION:
            raise ValueError("El refinamiento encontró demasiados registros. Reduce el rango de exploración.")
        registros.extend(nuevos)
    advertencias = (AVISO_EXPLORACION,) + ((AVISO_REFINAMIENTO_AGOTADO,) if agotado else ())
    return ResultadoExploracion(_ceros_unicos(registros), len(muestras), advertencias,
                                unidad_angular=entrada.unidad_angular, evaluaciones_refinamiento=evaluaciones,
                                refinamientos=refinamientos, refinamiento_agotado=agotado)


def _ceros_unicos(registros: list[CandidatoExploracion]) -> tuple[CandidatoExploracion, ...]:
    ceros = set()
    candidatos = []
    for registro in registros:
        if registro.tipo == "cero_evaluado":
            if registro.abscisa in ceros:
                continue
            ceros.add(registro.abscisa)
        candidatos.append(registro)
    return tuple(candidatos)
