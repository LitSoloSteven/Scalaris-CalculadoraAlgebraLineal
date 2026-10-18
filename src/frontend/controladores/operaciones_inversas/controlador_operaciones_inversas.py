"""Controlador para el cálculo de la matriz inversa y estructuración de pasos didácticos."""
from __future__ import annotations

import logging
import time

from src.backend.constantes import DIMENSION_MAXIMA_LATEX_INVERSA
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion
from src.frontend.controladores.operaciones_inversas.foco_paso import (
    construir_foco_paso,
)
from src.backend.resolutores.operaciones_matrices.captura_inversa import (
    construir_resultado_vacio,
    extraer_comprobaciones_inversa,
    validar_y_parsear_matriz_cuadrada,
)
from src.frontend.controladores.utilidades import parsear_carga_json

registro = logging.getLogger(__name__)


def _ejecutar_resolutor(matriz_a: Matriz) -> tuple[dict | None, float, str | None]:
    """Ejecuta el resolutor de inversa cronometrando el tiempo de cálculo."""
    t0 = time.perf_counter()
    try:
        resolutor = ResolutorInversa()
        resultado = resolutor.resolver(matriz_a, construir_detalle_latex=False)
        return resultado, time.perf_counter() - t0, None
    except ValueError as error:
        return None, time.perf_counter() - t0, str(error)
    except Exception:
        registro.exception("Error inesperado en ResolutorInversa")
        return None, time.perf_counter() - t0, "Ocurrió un error inesperado al calcular la inversa. Inténtalo de nuevo."


def _ensamblar_resultado_inversa(
    resultado: dict,
    matriz_a: Matriz,
    dimension: int,
    tiempo_s: float,
) -> dict:
    """Estructura la respuesta completa para la vista con pasos agrupados y verificaciones."""
    estado_calculo = resultado.get("estado", "ERROR")
    pasos_crudos = resultado.get("pasos", [])
    pasos_agrupados, grupos, estadisticas = agrupar_pasos_eliminacion(pasos_crudos, dimension, estado_calculo, contexto="inversa")

    determinante = resultado.get("determinante")
    inversa = resultado.get("inversa")
    latex_inv = matriz_a_latex(inversa) if (inversa is not None and dimension <= DIMENSION_MAXIMA_LATEX_INVERSA) else None
    latex_a = matriz_a_latex(matriz_a) if (dimension <= DIMENSION_MAXIMA_LATEX_INVERSA) else None
    verificaciones = extraer_comprobaciones_inversa(resultado, dimension) if estado_calculo == "EXITO" else []

    return {
        "estado": estado_calculo,
        "mensaje": resultado.get("mensaje", ""),
        "dimension": dimension,
        "tiempo_transcurrido_segundos": round(tiempo_s, 4),
        "determinante": determinante,
        "determinante_texto": formatear_fraccion_texto(determinante) if determinante is not None else None,
        "matriz_a": matriz_a,
        "matriz_a_latex": latex_a,
        "inversa": inversa,
        "inversa_latex": latex_inv,
        "pasos": pasos_agrupados,
        "grupos": grupos,
        "estadisticas": estadisticas,
        "comprobaciones": verificaciones,
        "celda_error": None,
    }


class ControladorOperacionesInversas:
    """Gestiona el cálculo paso a paso de la matriz inversa para visualización didáctica."""

    @classmethod
    def procesar_inversa(cls, carga_json: str) -> dict:
        """Devuelve la inversa y sus pasos, o un error estructurado si la carga falla."""
        datos_crudos, error_json = parsear_carga_json(carga_json)
        if error_json is not None or datos_crudos is None:
            return construir_resultado_vacio("ERROR", "Carga JSON inválida. Revisa los datos y vuelve a calcular.")

        matriz_a, dimension, error_resultado = validar_y_parsear_matriz_cuadrada(datos_crudos)
        if error_resultado is not None or matriz_a is None:
            return error_resultado or construir_resultado_vacio("ERROR", "Datos inválidos.")

        resultado, tiempo_s, error_ejecucion = _ejecutar_resolutor(matriz_a)
        if error_ejecucion is not None or resultado is None:
            return construir_resultado_vacio("ERROR", error_ejecucion or "Error al resolver.", opciones={'dimension': dimension, 'tiempo_s': tiempo_s, 'matriz_a': matriz_a})

        estado_calculo = resultado.get("estado", "ERROR")
        if estado_calculo in ("ERROR", "SINGULAR"):
            determinante = resultado.get("determinante")
            return construir_resultado_vacio(estado_calculo, resultado.get("mensaje", "Error al resolver."), opciones={'dimension': dimension, 'tiempo_s': tiempo_s, 'determinante': determinante, 'matriz_a': matriz_a})

        return _ensamblar_resultado_inversa(resultado, matriz_a, dimension, tiempo_s)

    @classmethod
    def construir_foco_paso(cls, pasos: list[dict], indice: int) -> dict:
        """Delega el cálculo de foco pedagógico al módulo especializado."""
        return construir_foco_paso(pasos, indice)
