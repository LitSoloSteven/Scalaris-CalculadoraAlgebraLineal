"""Integración real orientada con límites finitos o infinitos."""

from collections.abc import Callable
from math import fsum, isfinite

from src.backend.excepciones import ErrorDominio
from .cuadratura_kronrod import integrar_tramo
from .errores_numericos import ErrorCapacidadNumerica

_MAXIMO_MUESTRAS_POR_EVALUACION = 18000


class PresupuestoIntegral:
    """Acota la suma de muestras de todas las integrales de una evaluación de f(x)."""

    def __init__(self) -> None:
        """Inicializa el contador de muestras disponibles."""
        self._restantes = _MAXIMO_MUESTRAS_POR_EVALUACION

    def consumir(self) -> None:
        """Descuenta una muestra o lanza ErrorNoFinito si se agota el presupuesto."""
        self._restantes -= 1
        if self._restantes < 0:
            raise ErrorCapacidadNumerica(
                "La evaluación excede el máximo de muestras de integración. Simplifica la expresión.",
                "INTEGRAL_PRESUPUESTO_AGOTADO",
            )


def integrar_real(funcion: Callable[[float], float], inferior: float, superior: float) -> float:
    """Integra con signo y admite colas infinitas independientes; lanza errores numéricos controlados."""
    if inferior == superior and not isfinite(inferior):
        raise ErrorDominio("Los dos límites de integración no pueden ser el mismo infinito.")
    signo = 1 if inferior <= superior else -1
    inicio, fin = sorted((inferior, superior))
    try:
        resultado = signo * _integrar_ordenado(funcion, inicio, fin)
    except OverflowError as error:
        raise _error_capacidad() from error
    if not isfinite(resultado):
        raise _error_capacidad()
    return resultado


def _integrar_ordenado(funcion: Callable[[float], float], inicio: float, fin: float) -> float:
    if isfinite(inicio) and isfinite(fin):
        return integrar_tramo(funcion, inicio, fin)
    # Separa ambas colas para evitar que su cancelación parezca convergencia.
    if inicio < 0 < fin:
        return fsum((_integrar_ordenado(funcion, inicio, 0), _integrar_ordenado(funcion, 0, fin)))
    extremo, direccion = (inicio, 1) if isfinite(inicio) else (fin, -1)
    return integrar_tramo(_transformar_cola(funcion, extremo, direccion), 0.0, 1.0)


def _transformar_cola(funcion: Callable[[float], float], extremo: float, direccion: int) -> Callable[[float], float]:
    def transformada(distancia: float) -> float:
        # La distancia a cero se conserva aunque el refinamiento se acerque al infinito.
        desplazamiento = (1.0 - distancia) / distancia
        abscisa = extremo + direccion * desplazamiento
        if not isfinite(abscisa):
            raise _error_capacidad()
        valor = funcion(abscisa) / distancia / distancia
        if not isfinite(valor):
            raise _error_capacidad()
        return valor

    return transformada


def _error_capacidad() -> ErrorCapacidadNumerica:
    return ErrorCapacidadNumerica("La integral excede la capacidad numérica.")
