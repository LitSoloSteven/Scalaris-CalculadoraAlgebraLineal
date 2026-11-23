"""Validación de captura y análisis exacto de subespacios por generadores."""
from __future__ import annotations

from collections.abc import Mapping
import re

from src.backend.resolutores.operaciones_vectores.subespacios.captura_subespacios import (
    capturar_generadores,
)
from src.backend.resolutores.operaciones_vectores.subespacios.contrato_subespacios import (
    ErrorCapturaSubespacio,
)
from src.backend.resolutores.operaciones_vectores.subespacios.subespacios import (
    analizar_subespacio,
)
from src.frontend.controladores.algebra.operaciones_vectores.presentacion_subespacios import (
    presentar_resultado_subespacio,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    EJEMPLO_GENERADORES,
    MENSAJE_CAPTURA_VACIA,
    MODO_GENERADORES,
    PLANTILLA_COMPONENTE_VACIA,
)

_PATRON_COMPONENTE = re.compile(r"^vectores\.(.+)\.datos\[(\d+)\]$")


def ejemplo_generadores() -> dict[str, list[str]]:
    """Devuelve una copia del ejemplo inicial de tres generadores en ℝ³."""
    return {etiqueta: list(valores) for etiqueta, valores in EJEMPLO_GENERADORES.items()}


def analizar_generadores_desde_captura(captura: object) -> dict:
    """Valida la captura de generadores, invoca el motor y adapta su resultado."""
    diagnostico_vacio = _detectar_celdas_vacias(captura)
    if diagnostico_vacio is not None:
        return _resultado_entrada_invalida(captura, diagnostico_vacio)
    try:
        entrada = capturar_generadores(captura)
    except ErrorCapturaSubespacio as error:
        diagnostico = _diagnostico_desde_error(error)
        return _resultado_entrada_invalida(captura, diagnostico)
    resultado = analizar_subespacio(entrada)
    return presentar_resultado_subespacio(
        resultado, etiquetas=entrada["etiquetas"]
    )


def _es_celda_vacia(celda: object) -> bool:
    return celda is None or (isinstance(celda, str) and not celda.strip())


def _recolectar_vacias_vector(etiqueta: str, vector: object) -> tuple[int, list[tuple[str, int]]]:
    if not isinstance(vector, Mapping):
        return 0, []
    datos = vector.get("datos")
    if not isinstance(datos, (list, tuple)):
        return 0, []
    vacias = [(etiqueta, indice) for indice, celda in enumerate(datos) if _es_celda_vacia(celda)]
    return len(datos), vacias


def _detectar_celdas_vacias(captura: object) -> dict | None:
    if not isinstance(captura, Mapping):
        return None
    vectores = captura.get("vectores")
    if not isinstance(vectores, Mapping) or not vectores:
        return None
    total_celdas = 0
    vacias: list[tuple[str, int]] = []
    for etiqueta, vector in vectores.items():
        cantidad, faltantes = _recolectar_vacias_vector(str(etiqueta), vector)
        total_celdas += cantidad
        vacias.extend(faltantes)
    if not vacias:
        return None
    if len(vacias) == total_celdas:
        return _construir_diagnostico(MENSAJE_CAPTURA_VACIA, "vectores", None, None)
    etiqueta, componente = vacias[0]
    mensaje = PLANTILLA_COMPONENTE_VACIA.format(componente=componente + 1, etiqueta=etiqueta)
    return _construir_diagnostico(mensaje, f"vectores.{etiqueta}.datos[{componente}]", etiqueta, componente)


def _diagnostico_desde_error(error: ErrorCapturaSubespacio) -> dict:
    ubicacion = error.ubicacion
    base = str(error).split(" Ubicacion:", 1)[0].strip()
    if ubicacion:
        coincidencia = _PATRON_COMPONENTE.fullmatch(ubicacion)
        if coincidencia:
            etiqueta = coincidencia.group(1)
            componente = int(coincidencia.group(2))
            mensaje = f"Vector {etiqueta}, componente {componente + 1}: {base}"
            return _construir_diagnostico(mensaje, ubicacion, etiqueta, componente)
        if ubicacion.startswith("vectores."):
            etiqueta = ubicacion.removeprefix("vectores.").split(".", 1)[0]
            return _construir_diagnostico(base, ubicacion, etiqueta, None)
    return _construir_diagnostico(base, ubicacion, None, None)


def _construir_diagnostico(
    mensaje: str,
    ubicacion: str | None,
    etiqueta: str | None,
    componente: int | None,
) -> dict:
    return {
        "mensaje": mensaje,
        "ubicacion": ubicacion,
        "etiqueta": etiqueta,
        "componente": componente,
    }


def _resultado_entrada_invalida(captura: object, diagnostico: dict) -> dict:
    dimension = captura.get("dimension_ambiente") if isinstance(captura, Mapping) else None
    modo = captura.get("modo") if isinstance(captura, Mapping) else MODO_GENERADORES
    return presentar_resultado_subespacio(
        {
            "estado": "ERROR",
            "modo": modo or MODO_GENERADORES,
            "codigo": "ENTRADA_INVALIDA",
            "mensaje": diagnostico["mensaje"],
            "dimension_ambiente": dimension if type(dimension) is int else None,
        },
        diagnostico=diagnostico,
    )
