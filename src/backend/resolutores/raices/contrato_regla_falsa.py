"""Contrato de entrada y salida del motor de regla falsa."""
from dataclasses import dataclass, field
from typing import TypedDict

from .contrato_biseccion import (
    AVISO_INTERVALO_INVERTIDO,
    ContextoFallo,
    DiagnosticoBiseccion,
)
from .contrato_continuidad import InformeContinuidad
from .decision_biseccion import AccionBiseccion, SignoProducto
from .limites_raices import LIMITE_ITERACIONES_DEFECTO

AccionReglaFalsa = AccionBiseccion
DiagnosticoReglaFalsa = DiagnosticoBiseccion


class MetricasReglaFalsa(TypedDict, total=False):
    """Magnitudes y condicion de continuidad publicadas por el motor de regla falsa."""

    iteraciones_totales: int
    residuo_final: float
    continuidad: str


@dataclass(frozen=True)
class EntradaReglaFalsa:
    """Expresion, intervalo y tolerancia de residuo validados para falsa posicion."""

    expresion: str
    extremo_izquierdo: float
    extremo_derecho: float
    tolerancia: float
    limite_iteraciones: int = LIMITE_ITERACIONES_DEFECTO
    intervalo_invertido: bool = field(default=False, kw_only=True)
    unidad_angular: str = field(default="radianes", kw_only=True)

    @property
    def advertencias(self) -> tuple[str, ...]:
        """Devuelve el aviso de normalizacion conservado al revalidar la entrada canonica."""
        return (AVISO_INTERVALO_INVERTIDO,) if self.intervalo_invertido else ()


@dataclass(frozen=True)
class IteracionReglaFalsa:
    """Registro inmutable de una iteracion del metodo."""

    i: int
    extremo_izquierdo: float
    extremo_derecho: float
    c: float
    f_a: float
    f_b: float
    f_c: float
    ancho: float
    residuo: float
    error_relativo: str
    error_relativo_valor: float | None = None
    signo_producto: SignoProducto | None = None
    accion: AccionReglaFalsa | None = None
    motivo_parada: str = ""
    explicacion: str = ""


@dataclass(frozen=True)
class ResultadoReglaFalsa:
    """Resultado completo del metodo con estado, intervalo final y metricas."""

    estado: str
    mensaje: str
    aproximacion: float | None = None
    intervalo_final: tuple[float, float] | None = None
    tolerancia: float | None = None
    iteraciones: tuple[IteracionReglaFalsa, ...] = ()
    motivo_parada: str = ""
    metricas: MetricasReglaFalsa = field(default_factory=dict)
    codigo_diagnostico: str = ""
    advertencias: tuple[str, ...] = ()
    diagnostico: DiagnosticoReglaFalsa | None = None
    contexto_fallo: ContextoFallo | None = None
    unidad_angular: str = "radianes"
    informe_continuidad: InformeContinuidad | None = None