"""Delegación de la captura al motor real de regla falsa."""
from collections.abc import Mapping
from dataclasses import replace

from src.backend.resolutores.raices.contrato_regla_falsa import ResultadoReglaFalsa
from src.backend.resolutores.raices.regla_falsa import regla_falsa
from .captura import preparar_entrada
from .serializacion import serializar_resultado

_MENSAJE_EVALUACION = (
    "No se pudo evaluar f(x). Revisa la sintaxis, el dominio y la magnitud de los valores."
)


def resolver_captura(captura: Mapping[str, object]) -> dict:
    """Devuelve el sobre del motor o un error serializable de captura o adaptación."""
    try:
        entrada = preparar_entrada(captura)
    except ValueError as error:
        return _error_adaptacion(str(error), "ENTRADA_INVALIDA", "entrada_invalida")
    except (TypeError, OverflowError, RecursionError):
        return _error_adaptacion(_MENSAJE_EVALUACION, "ENTRADA_INVALIDA", "entrada_invalida")
    try:
        resultado = regla_falsa(entrada)
        advertencias = tuple(dict.fromkeys(entrada.advertencias + resultado.advertencias))
        return serializar_resultado(replace(resultado, advertencias=advertencias))
    except (ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError):
        return _error_adaptacion(_MENSAJE_EVALUACION, "ERROR_ADAPTACION", "error_adaptacion")


def _error_adaptacion(mensaje: str, codigo: str, motivo: str) -> dict:
    return serializar_resultado(ResultadoReglaFalsa(
        mensaje=mensaje, codigo_diagnostico=codigo, motivo_parada=motivo,
    ))
