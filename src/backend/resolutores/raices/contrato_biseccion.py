"""Contrato de entrada y salida del motor de bisección con precisión entera."""
import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TypedDict

from .criterios_biseccion import CriterioParada, tolerancia_decimal, validar_criterio, validar_entero_criterio
from .limites_biseccion import D_MAXIMO, LIMITE_ITERACIONES_DEFECTO, LIMITE_ITERACIONES_MAXIMO, LONGITUD_MAXIMA_EXPRESION


@dataclass(frozen=True)
class EntradaBiseccion:
    """Expresión, intervalo, precisión decimal y límite de iteraciones validados."""

    expresion: str
    extremo_izquierdo: float
    extremo_derecho: float
    decimales: int
    limite_iteraciones: int = LIMITE_ITERACIONES_DEFECTO
    criterio: CriterioParada | None = field(default=None, kw_only=True)

    @property
    def error_absoluto(self) -> Fraction:
        """Devuelve la tolerancia decimal exacta; otros criterios conservan el valor heredado."""
        precision = self.criterio.parametro if self.criterio and self.criterio.tipo == "decimales" else self.decimales
        return tolerancia_decimal(precision)

    @property
    def criterio_activo(self) -> CriterioParada:
        """Devuelve el criterio explícito o la precisión decimal de una captura antigua."""
        return self.criterio or CriterioParada("decimales", self.decimales)


@dataclass(frozen=True)
class IteracionBiseccion:
    """Registro inmutable de una iteración del método."""

    i: int
    extremo_izquierdo: float
    extremo_derecho: float
    c: float
    f_a: float
    f_b: float
    f_c: float
    ancho: float
    cota: float
    residuo: float
    error_relativo: str
    explicacion: str
    error_relativo_valor: float | None = None


class MetricasBiseccion(TypedDict, total=False):
    """Magnitudes y condición de continuidad publicadas por el motor numérico."""

    iteraciones_totales: int
    residuo_final: float
    continuidad: str


class DiagnosticoBiseccion(TypedDict):
    """Código, origen y mensaje de una restricción identificada sin inventar una abscisa."""

    codigo: str
    origen: str
    mensaje: str


class EvaluacionExtremo(TypedDict):
    """Evaluación individual finita o diagnóstico del extremo que se intentó evaluar."""

    abscisa: float
    valor: float | None
    codigo: str
    mensaje: str


class ContextoFallo(TypedDict, total=False):
    """Etapa, abscisa fallida e intervalo con extremos válidos disponibles al fallar."""

    etapa: str
    x_fallo: float | None
    intervalo_valido: tuple[float, float] | None
    extremos: tuple[EvaluacionExtremo, ...]


@dataclass(frozen=True)
class ResultadoBiseccion:
    """Resultado completo del método con estado, intervalo final y métricas."""

    estado: str
    mensaje: str
    aproximacion: float | None = None
    intervalo_final: tuple[float, float] | None = None
    error_absoluto: Fraction | None = None
    cota: float | None = None
    iteraciones: tuple[IteracionBiseccion, ...] = ()
    motivo_parada: str = ""
    metricas: MetricasBiseccion = field(default_factory=dict)
    codigo_diagnostico: str = ""
    criterio_solicitado: CriterioParada | None = None
    unidad_criterio: str = ""
    umbral: float | int | None = None
    metrica_final: float | int | None = None
    advertencias: tuple[str, ...] = ()
    diagnostico: DiagnosticoBiseccion | None = None
    contexto_fallo: ContextoFallo | None = None


def validar_precision(valor) -> int:
    """Rechaza decimales no entero, booleano o fuera de rango; devuelve el entero validado."""
    return validar_entero_criterio(valor, "La precisión decimales", D_MAXIMO)


def derivar_E(decimales: int) -> Fraction:
    """Devuelve 10^(-decimales) como fracción exacta; lanza ValueError si decimales es inválido."""
    return tolerancia_decimal(decimales)


def validar_entrada(datos: dict) -> EntradaBiseccion:
    """Valida una carga cruda y devuelve la entrada canónica; lanza ValueError granular."""
    if not isinstance(datos, dict):
        raise ValueError("La entrada debe ser un diccionario con la expresion y el intervalo.")
    expresion = _validar_expresion(datos.get("expresion"))
    extremo_izquierdo = _validar_extremo(datos.get("extremo_izquierdo"), "extremo_izquierdo")
    extremo_derecho = _validar_extremo(datos.get("extremo_derecho"), "extremo_derecho")
    if extremo_izquierdo >= extremo_derecho:
        raise ValueError(f"El intervalo es inválido: extremo_izquierdo ({extremo_izquierdo}) debe ser menor que extremo_derecho ({extremo_derecho}).")
    decimales = validar_precision(datos.get("decimales", 4) if datos.get("criterio") is not None else datos.get("decimales"))
    limite = _validar_limite(datos.get("limite_iteraciones"))
    criterio = validar_criterio(datos.get("criterio"), decimales, limite)
    return EntradaBiseccion(expresion=expresion, extremo_izquierdo=extremo_izquierdo,
                           extremo_derecho=extremo_derecho, decimales=decimales,
                           limite_iteraciones=limite, criterio=criterio)


def _validar_expresion(valor) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("La expresión f(x) es obligatoria y no puede estar vacía.")
    if len(valor) > LONGITUD_MAXIMA_EXPRESION:
        raise ValueError(f"La expresión excede {LONGITUD_MAXIMA_EXPRESION} caracteres.")
    return valor.strip()


def _validar_extremo(valor, nombre: str) -> float:
    if isinstance(valor, bool):
        raise ValueError(f"El extremo {nombre} no puede ser booleano.")
    if not isinstance(valor, (int, float)):
        raise ValueError(f"El extremo {nombre} debe ser numérico (recibido {valor!r}).")
    try:
        numero = float(valor)
    except OverflowError as error:
        raise ValueError(f"El extremo {nombre} excede la capacidad numérica.") from error
    if not math.isfinite(numero):
        raise ValueError(f"El extremo {nombre} debe ser finito (recibido {valor!r}).")
    return numero


def _validar_limite(valor) -> int:
    if valor is None:
        return LIMITE_ITERACIONES_DEFECTO
    if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= LIMITE_ITERACIONES_MAXIMO:
        raise ValueError(
            f"El límite de iteraciones debe ser un entero entre 1 y {LIMITE_ITERACIONES_MAXIMO} (recibido {valor!r})."
        )
    return valor
