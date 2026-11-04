"""Datos inmutables y validación de solicitudes de exploración real."""
import math
from dataclasses import dataclass

from .limites_biseccion import LONGITUD_MAXIMA_EXPRESION

AVISO_EXPLORACION = (
    "La exploración finita puede omitir raíces. Los candidatos no certifican raíces "
    "ni continuidad; reducir el paso puede revelar otros candidatos."
)


@dataclass(frozen=True)
class EntradaExploracion:
    """Expresión, extremos ordenados y paso de una malla real."""

    expresion: str
    x_min: float
    x_max: float
    paso: float


@dataclass(frozen=True)
class CandidatoExploracion:
    """Clasificación local con intervalo propio y muestra opcional finita."""

    tipo: str
    intervalo: tuple[float, float]
    abscisa: float | None = None
    valor: float | None = None
    mensaje: str = ""


@dataclass(frozen=True)
class ResultadoExploracion:
    """Registros acotados y número efectivo de evaluaciones, sin afirmar exhaustividad."""

    candidatos: tuple[CandidatoExploracion, ...]
    evaluaciones: int
    advertencias: tuple[str, ...] = (AVISO_EXPLORACION,)


def validar_exploracion(entrada: EntradaExploracion) -> EntradaExploracion:
    """Devuelve captura canónica; lanza ValueError ante forma, expresión o números inválidos."""
    if not isinstance(entrada, EntradaExploracion):
        raise ValueError("La exploración requiere una EntradaExploracion.")
    expresion = entrada.expresion
    if not isinstance(expresion, str) or not expresion.strip():
        raise ValueError("Escribe una función para explorar.")
    if len(expresion) > LONGITUD_MAXIMA_EXPRESION:
        raise ValueError("La función supera la longitud permitida.")
    minimo = _numero_finito(entrada.x_min)
    maximo = _numero_finito(entrada.x_max)
    paso = _numero_finito(entrada.paso)
    if minimo >= maximo or paso <= 0:
        raise ValueError("Usa x_min < x_max y un paso positivo.")
    return EntradaExploracion(expresion.strip(), minimo, maximo, paso)


def _numero_finito(valor: object) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError("Los extremos y el paso deben ser números finitos.")
    try:
        numero = float(valor)
    except OverflowError as error:
        raise ValueError("El número excede la capacidad de representación.") from error
    if not math.isfinite(numero):
        raise ValueError("Los extremos y el paso deben ser números finitos.")
    return numero
