"""Datos inmutables y validación de solicitudes de exploración real."""
import math
from dataclasses import dataclass, field

from .limites_biseccion import LONGITUD_MAXIMA_EXPRESION
from .unidades_angulares import validar_unidad_angular

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
    unidad_angular: str = field(default="radianes", kw_only=True)


@dataclass(frozen=True)
class EvidenciaContacto:
    """Escala inicial, consumo efectivo y motivo de cierre de una búsqueda local sin certificación."""

    valor_inicial: float
    escala_inicial: float
    evaluaciones: int
    refinamientos: int
    motivo: str


@dataclass(frozen=True)
class CandidatoExploracion:
    """Clasificación local con intervalo propio y muestra opcional finita."""

    tipo: str
    intervalo: tuple[float, float]
    abscisa: float | None = None
    valor: float | None = None
    mensaje: str = ""
    evidencia_contacto: EvidenciaContacto | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class MuestraExploracion:
    """Evaluación finita o fallo controlado en una posición de la malla."""

    abscisa: float
    valor: float | None
    mensaje: str = ""


@dataclass(frozen=True)
class ResultadoExploracion:
    """Registros acotados y número efectivo de evaluaciones, sin afirmar exhaustividad."""

    candidatos: tuple[CandidatoExploracion, ...]
    evaluaciones: int
    advertencias: tuple[str, ...] = (AVISO_EXPLORACION,)
    unidad_angular: str = "radianes"
    evaluaciones_refinamiento: int = field(default=0, kw_only=True)
    refinamientos: int = field(default=0, kw_only=True)
    refinamiento_agotado: bool = field(default=False, kw_only=True)


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
    return EntradaExploracion(expresion.strip(), minimo, maximo, paso,
                              unidad_angular=validar_unidad_angular(entrada.unidad_angular))


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
