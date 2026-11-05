"""Resolución acotada de candidatos con el mismo motor y sin mezclar sus trazas."""
import ast
import math
from collections.abc import Callable
from dataclasses import asdict, replace

from .biseccion import resolver_intervalo_preparado
from .contrato_biseccion import EntradaBiseccion, validar_entrada
from .contrato_exploracion import CandidatoExploracion
from .contrato_resolucion_multiple import (
    CandidatoResolucion, EntradaResolucionMultiple, ResolucionCandidato,
    ResultadoResolucionMultiple, validar_resolucion_multiple,
)
from .diagnostico_biseccion import preparar_intervalo
from .evaluador_funcion import compilar
from .gramatica_funcion import analizar_expresion
from .limites_resolucion_multiple import EVALUACIONES_AUXILIARES_CANDIDATO
from .unidades_angulares import opciones_unidad


def resolver_candidatos(entrada: EntradaResolucionMultiple) -> ResultadoResolucionMultiple:
    """Devuelve un resultado por identificador; lanza ValueError solo por configuración común inválida."""
    entrada = validar_resolucion_multiple(entrada)
    funcion = compilar(entrada.configuracion.expresion, **opciones_unidad(entrada.unidad_angular))
    arbol = analizar_expresion(entrada.configuracion.expresion)
    reserva = entrada.configuracion.limite_iteraciones + EVALUACIONES_AUXILIARES_CANDIDATO
    resultados = []
    reservadas = 0
    for registro in entrada.candidatos:
        if reservadas + reserva > entrada.presupuesto_evaluaciones:
            resultados.append(ResolucionCandidato(registro.identificador, "PRESUPUESTO_AGOTADO",
                              "No se ejecutó este candidato: no cabe en el presupuesto restante. Resuélvelo individualmente."))
            continue
        reservadas += reserva
        resultado = _resolver_candidato(entrada.configuracion, registro, funcion, arbol)
        resultados.append(replace(resultado, evaluaciones_reservadas=reserva))
    filas = sum(len(registro.resultado.iteraciones) for registro in resultados if registro.resultado is not None)
    return ResultadoResolucionMultiple(tuple(resultados), reservadas, filas,
                                      any(registro.estado == "PRESUPUESTO_AGOTADO" for registro in resultados),
                                      unidad_angular=entrada.unidad_angular)


def _resolver_candidato(configuracion: EntradaBiseccion, registro: CandidatoResolucion,
                       funcion: Callable[[float], float], arbol: ast.Expression) -> ResolucionCandidato:
    try:
        candidato = registro.candidato
        _validar_candidato(candidato)
        inferior, superior = candidato.intervalo
        entrada = validar_entrada(asdict(replace(configuracion, extremo_izquierdo=inferior,
                                  extremo_derecho=superior, intervalo_invertido=False)))
    except ValueError as error:
        return ResolucionCandidato(registro.identificador, "NO_APTO", str(error))
    preparado = preparar_intervalo(entrada, funcion, arbol)
    try:
        for muestra in preparado.evaluaciones:
            if muestra["codigo"]:
                raise ValueError(muestra["mensaje"])
        _comprobar_aptitud(candidato, tuple(muestra["valor"] for muestra in preparado.evaluaciones))
    except ValueError as error:
        return ResolucionCandidato(registro.identificador, "NO_APTO", str(error),
                                   informe_continuidad=preparado.informe)
    cero = candidato.abscisa if candidato.tipo == "cero_evaluado" else None
    resultado = resolver_intervalo_preparado(entrada, funcion, preparado, cero)
    return ResolucionCandidato(registro.identificador, resultado.estado, resultado.mensaje, entrada, resultado,
                               informe_continuidad=resultado.informe_continuidad)


def _validar_candidato(candidato: CandidatoExploracion) -> None:
    if not isinstance(candidato, CandidatoExploracion) or candidato.tipo not in ("cruce", "cero_evaluado"):
        raise ValueError("Solo se resuelven cruces de signo o ceros evaluados con un intervalo vecino válido.")
    intervalo = candidato.intervalo
    if not isinstance(intervalo, tuple) or len(intervalo) != 2:
        raise ValueError("El candidato requiere un intervalo de dos extremos.")
    if any(type(extremo) not in (int, float) for extremo in intervalo):
        raise ValueError("Los extremos del candidato deben ser números finitos.")
    if intervalo[0] >= intervalo[1]:
        raise ValueError("El intervalo del candidato debe cumplir a < b.")


def _comprobar_aptitud(candidato: CandidatoExploracion, valores: tuple[float, ...]) -> None:
    if candidato.tipo == "cero_evaluado":
        if type(candidato.abscisa) not in (int, float) or candidato.abscisa not in candidato.intervalo:
            raise ValueError("El cero evaluado debe pertenecer a un extremo del intervalo vecino.")
        if valores[candidato.intervalo.index(candidato.abscisa)] != 0:
            raise ValueError("La muestra indicada ya no evalúa a cero; vuelve a explorar.")
    if 0 not in valores and math.copysign(1, valores[0]) == math.copysign(1, valores[1]):
        raise ValueError("El candidato no tiene cambio de signo ni un cero evaluado; vuelve a explorar.")
