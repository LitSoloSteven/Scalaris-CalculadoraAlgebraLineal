"""Integración real orientada con límites finitos o infinitos."""

from collections.abc import Callable
from math import fsum, isfinite, sqrt

from src.backend.excepciones import ErrorDominio
from .cuadratura_kronrod import integrar_tramo
from .compartido.errores_numericos import ErrorCapacidadNumerica

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
        return _integrar_finito(funcion, inicio, fin)
    # Separa ambas colas para evitar que su cancelación parezca convergencia.
    if inicio < 0 < fin:
        return fsum((_integrar_desde_cero(funcion, -inicio, -1), _integrar_desde_cero(funcion, fin, 1)))
    extremo, direccion = (inicio, 1) if isfinite(inicio) else (fin, -1)
    return integrar_tramo(_transformar_cola(funcion, extremo, direccion), 0.0, 1.0)


def _integrar_desde_cero(funcion: Callable[[float], float], distancia: float, direccion: int) -> float:
    if distancia <= 1.0:
        inicio, fin = sorted((0.0, direccion * distancia))
        return _integrar_finito(funcion, inicio, fin)
    # Invierte el cambio racional para conservar resolución cerca de cero en tramos finitos largos.
    mitad = distancia / 2
    corte = 1.0 / (1.0 + mitad + sqrt(mitad) * sqrt(mitad + 2.0))
    return integrar_tramo(_transformar_cola(funcion, 0.0, direccion), corte, 1.0)


def _integrar_finito(funcion: Callable[[float], float], inicio: float, fin: float) -> float:
    if inicio == fin:
        return 0.0
    centro = inicio / 2 + fin / 2
    if not inicio < centro < fin:
        return integrar_tramo(funcion, inicio, fin, partir=False)
    segmentos = ((inicio, centro), (centro, fin))
    return fsum(
        integrar_tramo(_transformar_segmento(funcion, inferior, superior), 0.0, 1.0, partir=False)
        for inferior, superior in segmentos
    )


def _transformar_segmento(
    funcion: Callable[[float], float], inferior: float, superior: float,
) -> Callable[[float], float]:
    ancho = superior - inferior

    def _transformada(posicion: float) -> float:
        # El cambio cúbico suaviza singularidades integrables en ambos extremos.
        distancia = min(posicion, 1.0 - posicion)
        proporcion = distancia**2 * (3.0 - 2.0 * distancia)
        desplazamiento = ancho * proporcion
        abscisa = inferior + desplazamiento if posicion <= 0.5 else superior - desplazamiento
        jacobiano_relativo = 6.0 * distancia * (1.0 - distancia)
        escala = ancho * min(1.0, jacobiano_relativo)
        valor = funcion(abscisa) * escala * max(1.0, jacobiano_relativo)
        if not isfinite(valor):
            raise _error_capacidad()
        return valor

    return _transformada


def _transformar_cola(funcion: Callable[[float], float], extremo: float, direccion: int) -> Callable[[float], float]:
    def _transformada(distancia: float) -> float:
        # La distancia a cero se conserva aunque el refinamiento se acerque al infinito.
        complemento = 1.0 - distancia
        desplazamiento = complemento**2 / distancia
        abscisa = extremo + direccion * desplazamiento
        if not isfinite(abscisa):
            raise _error_capacidad()
        valor = (funcion(abscisa) * complemento / distancia) * (1.0 + distancia) / distancia
        if not isfinite(valor):
            raise _error_capacidad()
        return valor

    return _transformada


def _error_capacidad() -> ErrorCapacidadNumerica:
    return ErrorCapacidadNumerica("La integral excede la capacidad numérica.")
