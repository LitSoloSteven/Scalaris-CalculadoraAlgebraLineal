"""Cuadratura adaptativa de Gauss (7 puntos) y Kronrod (15 puntos)."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from heapq import heapify, heappop, heappush
from math import fsum
from sys import float_info

from .errores_numericos import ErrorCapacidadNumerica

# Nodos positivos y central con sus pesos de Kronrod y de Gauss, según QUADPACK DQK15.
_REGLA = (
    (0.9914553711208126, 0.02293532201052922, 0.0),
    (0.9491079123427585, 0.06309209262997855, 0.1294849661688697),
    (0.8648644233597691, 0.1047900103222502, 0.0),
    (0.7415311855993944, 0.1406532597155259, 0.2797053914892767),
    (0.5860872354676911, 0.1690047266392679, 0.0),
    (0.4058451513773972, 0.1903505780647854, 0.3818300505051189),
    (0.2077849550078985, 0.2044329400752989, 0.0),
    (0.0, 0.2094821410847278, 0.4179591836734694),
)
_TOLERANCIA_ABSOLUTA = 1e-11
_TOLERANCIA_RELATIVA = 1e-9
_MAXIMO_SUBDIVISIONES = 256
_CODIGO_CONVERGENCIA = "INTEGRAL_SIN_CONVERGENCIA"


@dataclass(order=True, frozen=True)
class _Tramo:
    prioridad: float
    extremos: tuple[float, float] = field(compare=False)
    resultado: float = field(compare=False)


def integrar_tramo(
    funcion: Callable[[float], float], inferior: float, superior: float, *, partir: bool = True,
) -> float:
    """Integra en extremos finitos ordenados; lanza ErrorNoFinito si no alcanza la tolerancia."""
    if inferior == superior:
        return 0.0
    tramos = list(_subdividir(funcion, (inferior, superior))) if partir else [_estimar(funcion, inferior, superior)]
    heapify(tramos)
    resultado = fsum(tramo.resultado for tramo in tramos)
    error = fsum(-tramo.prioridad for tramo in tramos)
    for _ in range(_MAXIMO_SUBDIVISIONES):
        if error <= max(_TOLERANCIA_ABSOLUTA, _TOLERANCIA_RELATIVA * abs(resultado)):
            return fsum(tramo.resultado for tramo in tramos)
        anterior = heappop(tramos)
        izquierda, derecha = _subdividir(funcion, anterior.extremos)
        heappush(tramos, izquierda)
        heappush(tramos, derecha)
        resultado = fsum((resultado, -anterior.resultado, izquierda.resultado, derecha.resultado))
        error = fsum((error, anterior.prioridad, -izquierda.prioridad, -derecha.prioridad))
    raise _error_convergencia()


def _centro(inferior: float, superior: float) -> float:
    amplitud = superior - inferior
    if amplitud == float("inf"):
        return inferior / 2 + superior / 2
    return inferior + amplitud / 2


def _subdividir(funcion: Callable[[float], float], extremos: tuple[float, float]) -> tuple[_Tramo, _Tramo]:
    inferior, superior = extremos
    centro = _centro(inferior, superior)
    if not inferior < centro < superior:
        raise _error_convergencia()
    return _estimar(funcion, inferior, centro), _estimar(funcion, centro, superior)


def _estimar(funcion: Callable[[float], float], inferior: float, superior: float) -> _Tramo:
    centro = _centro(inferior, superior)
    semiancho = superior - centro
    muestras = tuple(_muestras(funcion, centro, semiancho, (inferior, superior)))
    kronrod = fsum(peso * valor for valor, peso, _ in muestras)
    gauss = fsum(peso * valor for valor, _, peso in muestras)
    magnitud = fsum(peso * abs(valor) for valor, peso, _ in muestras)
    variacion = fsum(peso * abs(valor - kronrod / 2) for valor, peso, _ in muestras)
    error = _estimar_error(abs(kronrod - gauss), magnitud, variacion)
    return _Tramo(-error * semiancho, (inferior, superior), kronrod * semiancho)


def _muestras(
    funcion: Callable[[float], float], centro: float, semiancho: float, extremos: tuple[float, float],
) -> Iterator[tuple[float, float, float]]:
    inferior, superior = extremos
    for nodo, kronrod, gauss in _REGLA:
        abscisas = (centro - semiancho * nodo, centro + semiancho * nodo) if nodo else (centro,)
        for abscisa in abscisas:
            if not inferior < abscisa < superior:
                raise _error_convergencia()
            yield funcion(abscisa), kronrod, gauss


def _estimar_error(diferencia: float, magnitud: float, variacion: float) -> float:
    if variacion and diferencia and diferencia < variacion / 200:
        diferencia = variacion * (200 * (diferencia / variacion)) ** 1.5
    elif variacion and diferencia:
        diferencia = variacion
    return max(diferencia, 50 * float_info.epsilon * magnitud)


def _error_convergencia() -> ErrorCapacidadNumerica:
    return ErrorCapacidadNumerica(
        "No se pudo confirmar la convergencia de la integral. Revisa el integrando y los límites.",
        _CODIGO_CONVERGENCIA,
    )
