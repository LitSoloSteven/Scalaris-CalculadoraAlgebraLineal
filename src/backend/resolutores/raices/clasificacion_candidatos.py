"""Clasificación conservadora de vecinos sin multiplicar sus valores ni unir huecos."""
import math

from .contrato_exploracion import CandidatoExploracion, MuestraExploracion
from .dominio_intervalo import comprobar_dominio_intervalo
from .limites_exploracion import MAXIMO_REGISTROS_EXPLORACION

CONTRASTE_CONTACTO = 0.25
AVISO_CRUCE = "Cambio de signo muestreado; continuidad no certificada."
AVISO_CERO = "Cero evaluado aproximado; no constituye una prueba simbólica."
AVISO_CONTACTO = "Posible contacto con el eje; no certifica raíz ni multiplicidad y no admite bisección sin cambio de signo."


def clasificar_candidatos(expresion: str, muestras: tuple[MuestraExploracion, ...], *, unidad_angular: str = "radianes") -> tuple[CandidatoExploracion, ...]:
    """Clasifica la malla válida; lanza ValueError si los registros exceden el presupuesto."""
    registros = []
    for indice, muestra in enumerate(muestras):
        if muestra.valor == 0:
            _agregar(registros, _cero_con_vecino(expresion, muestras, indice, unidad_angular))
        if indice:
            _agregar(registros, _clasificar_segmento(expresion, muestras[indice - 1], muestra, unidad_angular))
        if 0 < indice < len(muestras) - 1:
            _agregar(registros, _posible_contacto(expresion, muestras[indice - 1:indice + 2], unidad_angular))
    return tuple(registros)


def _agregar(registros: list, candidato: CandidatoExploracion | None) -> None:
    if candidato is None:
        return
    if len(registros) >= MAXIMO_REGISTROS_EXPLORACION:
        raise ValueError("Hay demasiados registros; reduce el rango de exploración.")
    registros.append(candidato)


def _restriccion(expresion: str, intervalo: tuple[float, float], unidad: str) -> str:
    try:
        comprobar_dominio_intervalo(expresion, intervalo, unidad_angular=unidad)
    except ValueError as error:
        return str(error)
    return ""


def _clasificar_segmento(expresion: str, izquierda: MuestraExploracion, derecha: MuestraExploracion, unidad: str) -> CandidatoExploracion | None:
    intervalo = (izquierda.abscisa, derecha.abscisa)
    if izquierda.valor is None or derecha.valor is None:
        mensaje = izquierda.mensaje or derecha.mensaje
        return CandidatoExploracion("segmento_invalido", intervalo, mensaje=mensaje)
    restriccion = _restriccion(expresion, intervalo, unidad)
    if restriccion:
        return CandidatoExploracion("discontinuidad", intervalo, mensaje=restriccion)
    if izquierda.valor == 0 or derecha.valor == 0:
        return None
    if math.copysign(1, izquierda.valor) != math.copysign(1, derecha.valor):
        return CandidatoExploracion("cruce", intervalo, mensaje=AVISO_CRUCE)
    return None


def _cero_con_vecino(expresion: str, muestras: tuple, indice: int, unidad: str) -> CandidatoExploracion | None:
    muestra = muestras[indice]
    for vecino in muestras[max(0, indice - 1):indice] + muestras[indice + 1:indice + 2]:
        intervalo = tuple(sorted((muestra.abscisa, vecino.abscisa)))
        if vecino.valor is not None and not _restriccion(expresion, intervalo, unidad):
            return CandidatoExploracion("cero_evaluado", intervalo, muestra.abscisa, muestra.valor, AVISO_CERO)
    return None


def _posible_contacto(expresion: str, muestras: tuple, unidad: str) -> CandidatoExploracion | None:
    izquierda, centro, derecha = muestras
    valores = tuple(muestra.valor for muestra in muestras)
    if any(valor is None or valor == 0 for valor in valores):
        return None
    if len({math.copysign(1, valor) for valor in valores}) != 1:
        return None
    escala = min(abs(izquierda.valor), abs(derecha.valor))
    if abs(centro.valor) / escala > CONTRASTE_CONTACTO:
        return None
    intervalo = (izquierda.abscisa, derecha.abscisa)
    if _restriccion(expresion, intervalo, unidad):
        return None
    return CandidatoExploracion("posible_contacto", intervalo, centro.abscisa, centro.valor, AVISO_CONTACTO)
