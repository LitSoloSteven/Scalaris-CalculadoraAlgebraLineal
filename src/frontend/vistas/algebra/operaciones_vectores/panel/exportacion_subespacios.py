"""Adaptación de Espacios y subespacios al contrato compartido de exportación PDF."""
from __future__ import annotations

from src.frontend.componentes.exportacion_pdf.montaje.integracion import (
    completar_exportacion,
    identificador_raiz,
)
from src.frontend.controladores.exportacion_pdf.documento.vigencia import EnlacePDF
from src.frontend.nucleo.textos.textos_espacio_vectorial import MODO_PERSONALIZADO
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    MODO_RESTRICCIONES,
    NOMBRES_MODOS,
    PDF_ESTADOS_SUBESPACIOS,
)


def entrada_documental_subespacio(vista) -> dict:
    """Devuelve la captura vigente de generadores o restricciones para el PDF."""
    captura = vista.captura.obtener()
    modo = captura.get("modo", vista.modo)
    if modo == MODO_PERSONALIZADO:
        return {"modo": NOMBRES_MODOS[modo], "Conjunto": _entrada_conjunto(captura["conjunto"])}
    return _entrada_conjunto(captura)


def _entrada_conjunto(captura: dict) -> dict:
    modo = captura["modo"]
    datos = {
        "modo": NOMBRES_MODOS.get(modo, modo),
        "dimension_ambiente": f"ℝ^{captura.get('dimension_ambiente', '')}",
    }
    if modo == MODO_RESTRICCIONES:
        if captura.get("formato") == "ecuaciones":
            lineas = [
                linea.strip()
                for linea in str(captura.get("ecuaciones", "")).splitlines() if linea.strip()
            ]
            datos["ecuaciones"] = lineas or [""]
        else:
            datos["matriz_a"] = captura.get("matriz_a", [])
            datos["vector_b"] = captura.get("vector_b", [])
        return datos
    vectores = captura.get("vectores", {})
    datos["vectores"] = {
        etiqueta: list(vector.get("datos", ())) for etiqueta, vector in vectores.items()
    }
    return datos


def montar_exportacion_subespacio(vista, resultado: dict) -> None:
    """Monta el control PDF cuando el análisis es exitoso y exportable."""
    personalizada = resultado.get("modo") == MODO_PERSONALIZADO
    clasificacion = resultado.get("codigo" if personalizada else "clasificacion")
    if clasificacion not in PDF_ESTADOS_SUBESPACIOS:
        return
    if resultado.get("estado") != "EXITO" and not (personalizada and clasificacion == "LIMITE_ARITMETICO"):
        return
    contenedor = getattr(vista, "contenedor_resultados", None)
    if contenedor is None or contenedor.is_deleted:
        return
    resultado_pdf = {**resultado, "estado": clasificacion}

    def _leer_estado() -> tuple:
        """Devuelve el estado vigente del resultado mientras no sea invalidado."""
        actual = resultado_pdf if getattr(vista, "ultimo_resultado", None) is resultado else None
        return (contenedor, actual, getattr(vista, "_revision_captura", 0), getattr(vista, "_identificador_calculo", 0))

    enlace = EnlacePDF(
        vista, vista.captura.obtener, identificador_raiz(contenedor),
        leer_estado=_leer_estado, leer_entrada_documental=lambda: entrada_documental_subespacio(vista),
    )
    completar_exportacion(vista, "espacios_subespacios", resultado_pdf, enlace)
