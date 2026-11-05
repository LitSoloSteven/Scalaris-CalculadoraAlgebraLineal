"""Evidencia y política de continuidad para un intervalo cerrado."""
from typing import Literal, TypedDict

TipoEvidencia = Literal[
    "COBERTURA_ESTRUCTURAL", "RESTRICCION_ESTRUCTURAL", "FALLO_EXTREMO", "FALLO_INTERIOR",
    "ANALISIS_INSUFICIENTE", "SOSPECHA_TRAZA",
]


class EvidenciaContinuidad(TypedDict):
    """Observación acotada al intervalo y, cuando se conoce, a una abscisa."""

    tipo: TipoEvidencia
    codigo: str
    intervalo: tuple[float, float]
    abscisa: float | None
    detalle: str


class InformeContinuidad(TypedDict):
    """Admisión por continuidad, independiente de la aptitud por signo o criterio."""

    intervalo: tuple[float, float]
    unidad_angular: Literal["radianes", "grados"]
    estado: Literal["CONFIRMADA", "RESTRICCION_DETECTADA", "NO_VERIFICADA"]
    politica: Literal["PERMITIR", "ADVERTIR", "RECHAZAR"]
    evidencia: tuple[EvidenciaContinuidad, ...]
    mensaje: str
