"""Configuración explícita y metadatos de la ejecución ampliada de regla falsa."""
from dataclasses import dataclass
from typing import Literal

from .contrato_regla_falsa import EntradaReglaFalsa, ResultadoReglaFalsa
from .criterios_biseccion import CriterioParada

CumplimientoReglaFalsa = Literal["CUMPLIDO", "NO_CUMPLIDO", "CONTEO_COMPLETADO", "NO_APLICA"]


@dataclass(frozen=True)
class ConfiguracionReglaFalsa:
    """Agrupa entrada clásica, criterio solicitado y extremo cero opcional."""

    entrada: EntradaReglaFalsa
    criterio: CriterioParada
    cero_preferido: float | None = None


@dataclass(frozen=True)
class ResultadoReglaFalsaAmpliado:
    """Conserva el sobre clásico separado de la condición y su cumplimiento real."""

    resultado: ResultadoReglaFalsa
    criterio: CriterioParada
    cumplimiento: CumplimientoReglaFalsa
    metrica_final: float | int | None
    umbral: float | int
