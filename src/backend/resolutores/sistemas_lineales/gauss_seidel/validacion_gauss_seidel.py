"""Validación exacta de la entrada del método iterativo de Gauss-Seidel."""
from ..iterativos.validacion_iterativa import (
    EntradaPreparada as EntradaPreparadaGaussSeidel,
    FalloValidacion as FalloValidacionGaussSeidel,
    ParametrosValidacion,
    preparar_captura as _preparar_captura,
    preparar_entrada as _preparar_entrada,
)
from .contrato_gauss_seidel import DiagnosticoGaussSeidel
from .limites_gauss_seidel import (
    MAXIMO_BITS_ENTRADA_GAUSS_SEIDEL,
    MAXIMO_ITERACIONES_GAUSS_SEIDEL,
)

_PARAMETROS_VALIDACION_GAUSS_SEIDEL = ParametrosValidacion(
    nombre_metodo="Gauss-Seidel",
    maximo_iteraciones=MAXIMO_ITERACIONES_GAUSS_SEIDEL,
    maximo_bits_entrada=MAXIMO_BITS_ENTRADA_GAUSS_SEIDEL,
    crear_diagnostico=DiagnosticoGaussSeidel,
)


def preparar_entrada(
    entrada: object,
) -> EntradaPreparadaGaussSeidel | FalloValidacionGaussSeidel:
    """Valida la entrada completa y devuelve una instantánea o el fallo ubicado."""
    return _preparar_entrada(entrada, _PARAMETROS_VALIDACION_GAUSS_SEIDEL)


def preparar_captura(
    captura: object,
) -> EntradaPreparadaGaussSeidel | FalloValidacionGaussSeidel:
    """Valida las celdas crudas de A y usa un inicio cero cuando se omite el campo."""
    return _preparar_captura(captura, _PARAMETROS_VALIDACION_GAUSS_SEIDEL)
