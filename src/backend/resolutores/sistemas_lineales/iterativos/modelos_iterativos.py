"""Modelos y fábricas de diagnóstico compartidos por la validación iterativa."""
from collections.abc import Callable
from dataclasses import dataclass

from .contrato_iterativo import (
    CampoIterativo, CodigoIterativo, DiagnosticoIterativo, EntradaCanonicaIterativa,
)


@dataclass(frozen=True, kw_only=True)
class ParametrosValidacion:
    """Reúne el nombre visible, los topes y la fábrica de diagnósticos del método."""

    nombre_metodo: str
    maximo_iteraciones: int
    maximo_bits_entrada: int
    crear_diagnostico: Callable[..., DiagnosticoIterativo]


@dataclass(frozen=True, kw_only=True)
class EntradaPreparada(EntradaCanonicaIterativa):
    """Instantánea inmutable de A, b, el inicio y los parámetros ya validados."""


@dataclass(frozen=True, kw_only=True)
class FalloValidacion:
    """Fallo de entrada con su código, diagnóstico y dominancia si pudo evaluarse."""

    codigo: CodigoIterativo
    diagnostico: DiagnosticoIterativo
    dominancia_estricta: bool | None = None


@dataclass(frozen=True, kw_only=True)
class DatosValidacion:
    """Agrupa los campos crudos que se validan antes de construir la instantánea."""

    matriz: object
    vector_b: object
    vector_inicial: object
    tolerancia: object
    maximo_iteraciones: object


def crear_fallo(
    parametros: ParametrosValidacion,
    campo: CampoIterativo,
    mensaje: str,
    fila: int | None = None,
    columna: int | None = None,
) -> FalloValidacion:
    """Construye un fallo de entrada con el campo y las coordenadas conocidas."""
    return FalloValidacion(
        codigo="ENTRADA_INVALIDA",
        diagnostico=parametros.crear_diagnostico(
            mensaje=mensaje, campo=campo, fila=fila, columna=columna,
        ),
    )


def crear_fallo_cuadricula(
    parametros: ParametrosValidacion, mensaje: str, fila: int | None = None,
) -> FalloValidacion:
    """Construye un fallo de forma de A con el diagnóstico propio del método."""
    return FalloValidacion(
        codigo="ENTRADA_INVALIDA",
        diagnostico=parametros.crear_diagnostico(
            mensaje=mensaje, campo="matriz_a", fila=fila,
        ),
    )
