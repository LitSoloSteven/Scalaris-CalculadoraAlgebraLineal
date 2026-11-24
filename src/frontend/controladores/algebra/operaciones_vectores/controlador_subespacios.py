"""Validación de captura y análisis exacto de subespacios por generadores o restricciones."""
from __future__ import annotations

from collections.abc import Mapping
import re

from src.backend.resolutores.operaciones_vectores.subespacios.captura_subespacios import (
    capturar_generadores,
    capturar_restricciones,
)
from src.backend.resolutores.operaciones_vectores.subespacios.contrato_subespacios import (
    ErrorCapturaSubespacio,
)
from src.backend.resolutores.operaciones_vectores.subespacios.subespacios import (
    analizar_subespacio,
)
from src.frontend.controladores.algebra.operaciones_vectores.captura_restricciones import (
    ErrorCapturaRestricciones,
    diagnostico_restricciones_desde_error,
    interpretar_ecuaciones_restricciones,
)
from src.frontend.controladores.algebra.operaciones_vectores.presentacion_restricciones import (
    presentar_resultado_restricciones,
)
from src.frontend.controladores.algebra.operaciones_vectores.presentacion_subespacios import (
    presentar_resultado_subespacio,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    EJEMPLO_GENERADORES,
    MENSAJE_CAPTURA_VACIA,
    MENSAJE_RESTRICCIONES_VACIAS,
    MODO_GENERADORES,
    MODO_RESTRICCIONES,
    NOMBRES_MODOS,
    PLANTILLA_COMPONENTE_VACIA,
)

_PATRON_COMPONENTE = re.compile(r"^vectores\.(.+)\.datos\[(\d+)\]$")


def normalizar_modo_subespacios(modo: object) -> str:
    """Devuelve el modo admitido por Espacios y subespacios o generadores por defecto."""
    return modo if isinstance(modo, str) and modo in NOMBRES_MODOS else MODO_GENERADORES


def ejemplo_generadores() -> dict[str, list[str]]:
    """Devuelve una copia del ejemplo inicial de tres generadores en ℝ³."""
    return {etiqueta: list(valores) for etiqueta, valores in EJEMPLO_GENERADORES.items()}


def analizar_subespacio_desde_captura(captura: object) -> dict:
    """Despacha el análisis exacto al modo declarado en la captura vigente."""
    if isinstance(captura, Mapping) and captura.get("modo") == MODO_RESTRICCIONES:
        return analizar_restricciones_desde_captura(captura)
    return analizar_generadores_desde_captura(captura)


def analizar_generadores_desde_captura(captura: object) -> dict:
    """Valida la captura de generadores, invoca el motor y adapta su resultado."""
    diagnostico_vacio = diagnosticar_generadores_vacios(captura)
    if diagnostico_vacio is not None:
        return _resultado_entrada_invalida(captura, diagnostico_vacio)
    try:
        entrada = capturar_generadores(captura)
    except ErrorCapturaSubespacio as error:
        diagnostico = diagnosticar_error_generadores(error)
        return _resultado_entrada_invalida(captura, diagnostico)
    resultado = analizar_subespacio(entrada)
    return presentar_resultado_subespacio(
        resultado, etiquetas=entrada["etiquetas"]
    )


def analizar_restricciones_desde_captura(captura: object) -> dict:
    """Valida captura en Matriz o Ecuaciones, invoca el motor y adapta su resultado."""
    formato = str(captura.get("formato") or "matriz") if isinstance(captura, Mapping) else "matriz"
    try:
        datos_entrada = preparar_captura_restricciones(captura, formato)
        entrada = capturar_restricciones(datos_entrada)
    except ErrorCapturaRestricciones as error:
        return _resultado_entrada_invalida(captura, error.diagnostico)
    except ErrorCapturaSubespacio as error:
        return _resultado_entrada_invalida(captura, diagnostico_restricciones_desde_error(error, formato))
    resultado = analizar_subespacio(entrada)
    if resultado.get("estado") == "EXITO":
        return presentar_resultado_restricciones(resultado)
    return presentar_resultado_subespacio(resultado)


def preparar_captura_restricciones(captura: object, formato: str) -> dict:
    """Prepara la entrada Matriz/Ecuaciones que admite el motor exacto."""
    if not isinstance(captura, Mapping):
        raise ErrorCapturaRestricciones("La captura de restricciones es inválida.")
    dimension = captura.get("dimension_ambiente")
    if formato == "ecuaciones":
        interpretada = interpretar_ecuaciones_restricciones(captura.get("ecuaciones", ""), dimension)
        return {
            "modo": MODO_RESTRICCIONES,
            "dimension_ambiente": interpretada.dimension_ambiente,
            "matriz_a": interpretada.matriz_a,
            "vector_b": interpretada.vector_b,
        }
    matriz_a = captura.get("matriz_a")
    vector_b = captura.get("vector_b")
    if captura.get("matriz_vacia") or _matriz_restricciones_vacia(matriz_a, vector_b):
        raise ErrorCapturaRestricciones(
            MENSAJE_RESTRICCIONES_VACIAS,
            {
                "mensaje": MENSAJE_RESTRICCIONES_VACIAS,
                "ubicacion": "matriz_a",
                "campo": "matriz_a",
                "fila": None,
                "columna": None,
                "etiqueta": None,
                "componente": None,
            },
        )
    return {
        "modo": MODO_RESTRICCIONES,
        "dimension_ambiente": dimension,
        "matriz_a": matriz_a,
        "vector_b": vector_b,
    }


def _matriz_restricciones_vacia(matriz_a: object, vector_b: object) -> bool:
    if not isinstance(matriz_a, (list, tuple)) or not isinstance(vector_b, (list, tuple)):
        return False
    if not matriz_a and not vector_b:
        return False
    celdas_a = [celda for fila in matriz_a if isinstance(fila, (list, tuple)) for celda in fila]
    return all(_es_celda_vacia(celda) for celda in [*celdas_a, *vector_b])


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


def diagnosticar_generadores_vacios(captura: object) -> dict | None:
    """Identifica el primer generador incompleto o la captura totalmente vacía."""
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


def diagnosticar_error_generadores(error: ErrorCapturaSubespacio) -> dict:
    """Adapta la ubicación del error de dominio al panel de generadores."""
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
