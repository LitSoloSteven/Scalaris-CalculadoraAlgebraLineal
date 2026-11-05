"""Contratos inmutables de un lote y de sus resultados por candidato."""
from dataclasses import asdict, dataclass

from .contrato_biseccion import EntradaBiseccion, ResultadoBiseccion, validar_entrada
from .contrato_exploracion import AVISO_EXPLORACION, CandidatoExploracion
from .limites_resolucion_multiple import (
    LONGITUD_IDENTIFICADOR_CANDIDATO, MAXIMO_CANDIDATOS_MULTIPLE, MAXIMO_EVALUACIONES_MULTIPLE,
)


@dataclass(frozen=True)
class CandidatoResolucion:
    """Identificador estable y registro exploratorio que se comprobará de nuevo antes de resolver."""

    identificador: str
    candidato: CandidatoExploracion


@dataclass(frozen=True)
class EntradaResolucionMultiple:
    """Configuración común, candidatos independientes y presupuesto de reserva global."""

    configuracion: EntradaBiseccion
    candidatos: tuple[CandidatoResolucion, ...]
    presupuesto_evaluaciones: int = MAXIMO_EVALUACIONES_MULTIPLE
    unidad_angular: str = "radianes"


@dataclass(frozen=True)
class ResolucionCandidato:
    """Estado individual con su entrada/traza opcionales y reserva conservadora de evaluaciones."""

    identificador: str
    estado: str
    mensaje: str
    entrada: EntradaBiseccion | None = None
    resultado: ResultadoBiseccion | None = None
    evaluaciones_reservadas: int = 0


@dataclass(frozen=True)
class ResultadoResolucionMultiple:
    """Resultados separados, reserva total y filas efectivas sin certificar exhaustividad."""

    resultados: tuple[ResolucionCandidato, ...]
    evaluaciones_reservadas: int
    filas_generadas: int
    presupuesto_agotado: bool
    advertencias: tuple[str, ...] = (AVISO_EXPLORACION,)
    unidad_angular: str = "radianes"


def validar_resolucion_multiple(entrada: EntradaResolucionMultiple) -> EntradaResolucionMultiple:
    """Devuelve configuración canónica o lanza ValueError por forma, recursos o identificadores."""
    if not isinstance(entrada, EntradaResolucionMultiple) or not isinstance(entrada.configuracion, EntradaBiseccion):
        raise ValueError("El lote requiere una configuración de bisección válida.")
    if not isinstance(entrada.candidatos, tuple) or not 1 <= len(entrada.candidatos) <= MAXIMO_CANDIDATOS_MULTIPLE:
        raise ValueError(f"Selecciona entre 1 y {MAXIMO_CANDIDATOS_MULTIPLE} candidatos; reduce la exploración o resuelve uno.")
    presupuesto = entrada.presupuesto_evaluaciones
    if type(presupuesto) is not int or not 1 <= presupuesto <= MAXIMO_EVALUACIONES_MULTIPLE:
        raise ValueError(f"El presupuesto del lote debe ser un entero entre 1 y {MAXIMO_EVALUACIONES_MULTIPLE}.")
    if entrada.unidad_angular != "radianes":
        raise ValueError("La resolución múltiple admite radianes en la configuración actual.")
    _validar_identificadores(entrada.candidatos)
    configuracion = validar_entrada(asdict(entrada.configuracion))
    return EntradaResolucionMultiple(configuracion, entrada.candidatos, presupuesto, entrada.unidad_angular)


def _validar_identificadores(candidatos: tuple[CandidatoResolucion, ...]) -> None:
    identificadores = set()
    for registro in candidatos:
        if not isinstance(registro, CandidatoResolucion):
            raise ValueError("Cada candidato debe incluir un identificador y su registro exploratorio.")
        identificador = registro.identificador
        if not isinstance(identificador, str) or not identificador.strip() or len(identificador) > LONGITUD_IDENTIFICADOR_CANDIDATO:
            raise ValueError("Usa identificadores de candidato no vacíos y dentro de la longitud permitida.")
        if identificador in identificadores:
            raise ValueError("Los identificadores de los candidatos no pueden repetirse.")
        identificadores.add(identificador)
