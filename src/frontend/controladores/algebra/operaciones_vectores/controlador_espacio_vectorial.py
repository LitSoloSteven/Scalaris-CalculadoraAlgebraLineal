"""Puente entre el editor de términos y el verificador exacto de espacios."""
from collections.abc import Mapping

from src.backend.resolutores.operaciones_vectores.espacios_vectoriales.captura_espacio_vectorial import (
    capturar_espacio_vectorial,
)
from src.backend.resolutores.operaciones_vectores.espacios_vectoriales.contrato_espacio_vectorial import (
    ErrorCapturaEspacioVectorial,
)
from src.backend.resolutores.operaciones_vectores.espacios_vectoriales.espacios_vectoriales import (
    analizar_espacio_vectorial,
)
from src.backend.resolutores.operaciones_vectores.subespacios.contrato_subespacios import ErrorCapturaSubespacio
from src.frontend.nucleo.textos.textos_espacio_vectorial import (
    MODO_PERSONALIZADO, NOMBRES_OPERACIONES, VEREDICTOS,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import MODO_RESTRICCIONES
from .captura_restricciones import ErrorCapturaRestricciones, diagnostico_restricciones_desde_error
from .controlador_subespacios import (
    diagnosticar_error_generadores, diagnosticar_generadores_vacios, preparar_captura_restricciones,
)
from .presentacion_espacio_vectorial import formatear_polinomios, variables_operacion


def _exponente(texto: str) -> int | str:
    if texto.isascii() and texto.isdecimal() and len(texto) <= 2:
        return int(texto)
    return texto


def _preparar_operacion(coordenadas: list, cantidad_variables: int) -> list:
    return [
        [
            {"coeficiente": termino["coeficiente"],
             "exponentes": _separar_exponentes(termino["exponentes"], cantidad_variables)}
            for termino in terminos
        ]
        for terminos in coordenadas
    ]


def _separar_exponentes(datos: object, cantidad_variables: int) -> list:
    if not isinstance(datos, str):
        return []
    return [_exponente(texto) for texto in datos.split(maxsplit=cantidad_variables)]


def _resultado_invalido(diagnostico: dict) -> dict:
    return {
        "modo": MODO_PERSONALIZADO, "estado": "ERROR", "codigo": "ENTRADA_INVALIDA",
        "es_espacio_vectorial": None, "veredicto": VEREDICTOS[None],
        "diagnostico": diagnostico, "comprobaciones": (), "vector_cero": None,
        "operaciones": {}, "dimension_ambiente": None,
    }


def _error_conjunto(error: ErrorCapturaEspacioVectorial, formato: str | None) -> dict:
    diagnostico = error.diagnostico
    causa = error.__cause__
    if not isinstance(causa, ErrorCapturaSubespacio):
        return diagnostico
    detalle = (
        diagnostico_restricciones_desde_error(causa, formato)
        if formato else diagnosticar_error_generadores(causa)
    )
    return {**detalle, "origen": "conjunto"}


def analizar_espacio_desde_captura(captura: dict) -> dict:
    """Convierte los borradores en datos de dominio y adapta veredicto y evidencia exactos."""
    conjunto = captura["conjunto"]
    formato = conjunto.get("formato", "matriz") if conjunto.get("modo") == MODO_RESTRICCIONES else None
    vacio = diagnosticar_generadores_vacios(conjunto) if formato is None else None
    if vacio is not None:
        return _resultado_invalido({**vacio, "origen": "conjunto"})
    try:
        entrada = capturar_espacio_vectorial(_preparar_captura(captura, conjunto, formato))
    except ErrorCapturaRestricciones as error:
        return _resultado_invalido({**error.diagnostico, "origen": "conjunto"})
    except ErrorCapturaEspacioVectorial as error:
        return _resultado_invalido(_error_conjunto(error, formato))
    resultado = analizar_espacio_vectorial(entrada)
    dimension = entrada["conjunto"]["dimension_ambiente"]
    return {
        **resultado, "modo": MODO_PERSONALIZADO, "dimension_ambiente": dimension,
        "veredicto": VEREDICTOS[resultado["es_espacio_vectorial"]],
        "operaciones": _formatear_operaciones(entrada, dimension),
    }


def _preparar_captura(captura: dict, conjunto: dict, formato: str | None) -> dict:
    dimension = conjunto["dimension_ambiente"]
    return {
        "conjunto": preparar_captura_restricciones(conjunto, formato) if formato else conjunto,
        **{
            campo: _preparar_operacion(captura[campo], len(variables_operacion(campo, dimension)))
            for campo in NOMBRES_OPERACIONES
        },
    }


def _formatear_operaciones(entrada: Mapping, dimension: int) -> dict[str, tuple[str, ...]]:
    return {
        campo: formatear_polinomios(entrada[campo], variables_operacion(campo, dimension))
        for campo in NOMBRES_OPERACIONES
    }
