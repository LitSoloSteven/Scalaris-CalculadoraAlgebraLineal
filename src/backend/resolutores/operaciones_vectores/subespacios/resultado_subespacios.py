"""Construccion del contrato de resultado y de sus estados de error."""
from collections.abc import Mapping

from src.backend.constantes import ERROR, EXITO
from .contrato_subespacios import (
    MODO_GENERADORES,
    MODO_RESTRICCIONES,
    ErrorCapturaSubespacio,
    ResultadoSubespacio,
    validar_dimension_ambiente,
)


def resultado_inicial(modo: str | None, dimension: int | None) -> ResultadoSubespacio:
    """Devuelve el resultado con todas las claves y los valores neutros de un analisis vacio."""
    return {
        "estado": EXITO,
        "modo": modo,
        "clasificacion": None,
        "codigo": "",
        "mensaje": "",
        "dimension_ambiente": dimension,
        "es_subespacio": None,
        "contiene_origen": None,
        "es_vacio": None,
        "rango": None,
        "rango_aumentada": None,
        "base": None,
        "dimension": None,
        "indices_generadores_base": (),
        "etiquetas_generadores_base": (),
        "columnas_pivote": (),
        "columnas_libres": (),
        "particular": None,
        "direcciones": None,
        "dimension_afin": None,
        "testigo": None,
        "matriz_original": None,
        "matriz_reducida": None,
        "pasos": (),
        "comprobaciones": (),
    }


def resultado_error(
    entrada: object, codigo: str, mensaje: str
) -> ResultadoSubespacio:
    """Devuelve el resultado de error conservando modo y dimension solo cuando son legibles."""
    modo = None
    dimension = None
    if isinstance(entrada, Mapping):
        modo_crudo = entrada.get("modo")
        if modo_crudo in (MODO_GENERADORES, MODO_RESTRICCIONES):
            modo = modo_crudo
        try:
            dimension = validar_dimension_ambiente(entrada.get("dimension_ambiente"))
        except ErrorCapturaSubespacio:
            dimension = None
    resultado = resultado_inicial(modo, dimension)
    resultado.update({"estado": ERROR, "codigo": codigo, "mensaje": mensaje})
    return resultado
