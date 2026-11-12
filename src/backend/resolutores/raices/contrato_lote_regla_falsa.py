"""Contratos inmutables y validación global de lotes de falsa posición."""
from dataclasses import asdict, dataclass
from typing import Literal

from .contrato_continuidad import InformeContinuidad
from .contrato_exploracion import AVISO_EXPLORACION
from .contrato_regla_falsa import EntradaReglaFalsa
from .contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa, ResultadoReglaFalsaAmpliado
from .contrato_resolucion_multiple import CandidatoResolucion, validar_seleccion_multiple
from .criterios_regla_falsa import validar_criterio_regla_falsa
from .gramatica_funcion import analizar_expresion
from .limites_resolucion_multiple import MAXIMO_EVALUACIONES_MULTIPLE
from .validacion_regla_falsa import validar_entrada_regla_falsa

EstadoCandidatoReglaFalsa = Literal[
    "EXITO", "SIN_CAMBIO_DE_SIGNO", "ESTANCAMIENTO", "LIMITE_ITERACIONES",
    "ERROR", "NO_APTO", "PRESUPUESTO_AGOTADO",
]


@dataclass(frozen=True)
class EntradaLoteReglaFalsa:
    """Configuración común y candidatos con reserva global, sin una segunda unidad angular."""

    configuracion: ConfiguracionReglaFalsa
    candidatos: tuple[CandidatoResolucion, ...]
    presupuesto_evaluaciones: int = MAXIMO_EVALUACIONES_MULTIPLE


@dataclass(frozen=True)
class ResolucionCandidatoReglaFalsa:
    """Estado por identificador con respuesta ampliada e informe independientes opcionales."""

    identificador: str
    estado: EstadoCandidatoReglaFalsa
    mensaje: str
    respuesta: ResultadoReglaFalsaAmpliado | None = None
    evaluaciones_reservadas: int = 0
    informe_continuidad: InformeContinuidad | None = None


@dataclass(frozen=True)
class ResultadoLoteReglaFalsa:
    """Conserva orden, reservas conservadoras y filas efectivas sin medir evaluaciones reales."""

    resultados: tuple[ResolucionCandidatoReglaFalsa, ...]
    evaluaciones_reservadas: int
    filas_generadas: int
    presupuesto_agotado: bool
    advertencias: tuple[str, ...] = (AVISO_EXPLORACION,)


def validar_lote_regla_falsa(entrada: EntradaLoteReglaFalsa) -> EntradaLoteReglaFalsa:
    """Devuelve un lote canónico; lanza ValueError por configuración o selección global inválida."""
    if not isinstance(entrada, EntradaLoteReglaFalsa):
        raise ValueError("El lote debe cumplir el contrato de regla falsa.")
    configuracion = entrada.configuracion
    if not isinstance(configuracion, ConfiguracionReglaFalsa) or not isinstance(configuracion.entrada, EntradaReglaFalsa):
        raise ValueError("El lote requiere una configuración ampliada de regla falsa.")
    validar_seleccion_multiple(entrada.candidatos, entrada.presupuesto_evaluaciones)
    canonica = validar_entrada_regla_falsa(asdict(configuracion.entrada))
    criterio = validar_criterio_regla_falsa(configuracion.criterio, canonica.limite_iteraciones)
    analizar_expresion(canonica.expresion)
    return EntradaLoteReglaFalsa(ConfiguracionReglaFalsa(canonica, criterio),
                               entrada.candidatos, entrada.presupuesto_evaluaciones)
