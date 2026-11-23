"""Validación exacta de la entrada del método iterativo de Jacobi."""
from ..iterativos.validacion_iterativa import (
    EntradaPreparada as EntradaPreparadaJacobi,
    FalloValidacion as FalloValidacionJacobi,
    ParametrosValidacion,
    preparar_captura as _preparar_captura,
    preparar_entrada as _preparar_entrada,
)
from .contrato_jacobi import DiagnosticoJacobi, EntradaJacobi
from .limites_jacobi import MAXIMO_BITS_ENTRADA_JACOBI, MAXIMO_ITERACIONES_JACOBI

_PARAMETROS_VALIDACION_JACOBI = ParametrosValidacion(
    nombre_metodo="Jacobi",
    maximo_iteraciones=MAXIMO_ITERACIONES_JACOBI,
    maximo_bits_entrada=MAXIMO_BITS_ENTRADA_JACOBI,
    crear_diagnostico=DiagnosticoJacobi,
)


def preparar_entrada(
    entrada: object,
) -> EntradaPreparadaJacobi | FalloValidacionJacobi:
    """Valida la entrada completa y devuelve una instantánea o el fallo ubicado."""
    return _preparar_entrada(entrada, _PARAMETROS_VALIDACION_JACOBI, EntradaJacobi)


def preparar_captura(
    captura: object,
) -> EntradaPreparadaJacobi | FalloValidacionJacobi:
    """Valida las celdas crudas de A y usa un inicio cero cuando se omite el campo."""
    return _preparar_captura(captura, _PARAMETROS_VALIDACION_JACOBI)
