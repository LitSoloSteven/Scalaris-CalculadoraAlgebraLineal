"""Controlador para el cálculo de la matriz inversa y estructuración de pasos didácticos."""
from __future__ import annotations

import logging
import time

from src.backend.constantes import DIMENSION_MAXIMA_LATEX_INVERSA
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.utilidades.formateadores import formatear_fraccion_str
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion
from src.frontend.controladores.operaciones_inversas.foco_paso import (
    construir_foco_paso,
)
from src.frontend.controladores.operaciones_inversas.validador_inversa import (
    construir_resultado_vacio,
    extraer_comprobaciones_inversa,
    validar_y_parsear_matriz_cuadrada,
)
from src.frontend.controladores.utilidades import parsear_payload

logger = logging.getLogger(__name__)


def _ejecutar_resolutor(matriz_a: Matriz) -> tuple[dict | None, float, str | None]:
    """Ejecuta el resolutor de inversa cronometrando el tiempo de cálculo."""
    t0 = time.perf_counter()
    try:
        resolutor = ResolutorInversa()
        res = resolutor.resolver(matriz_a, build_step_latex=False)
        return res, time.perf_counter() - t0, None
    except ValueError as e:
        return None, time.perf_counter() - t0, str(e)
    except Exception:
        logger.exception("Error inesperado en ResolutorInversa")
        return None, time.perf_counter() - t0, "Ocurrió un error inesperado al calcular la inversa. Inténtalo de nuevo."


def _ensamblar_resultado_inversa(
    res: dict,
    matriz_a: Matriz,
    n: int,
    tiempo_s: float,
) -> dict:
    """Estructura la respuesta completa para la vista con pasos agrupados y verificaciones."""
    status = res.get("status", "ERROR")
    pasos_crudos = res.get("steps", [])
    pasos_agrupados, grupos, stats = agrupar_pasos_eliminacion(pasos_crudos, n, status, contexto="inversa")

    det = res.get("determinant")
    inversa = res.get("inverse")
    latex_inv = matriz_a_latex(inversa) if (inversa is not None and n <= DIMENSION_MAXIMA_LATEX_INVERSA) else None
    latex_a = matriz_a_latex(matriz_a) if (n <= DIMENSION_MAXIMA_LATEX_INVERSA) else None
    verificaciones = extraer_comprobaciones_inversa(res, n) if status == "SUCCESS" else []

    return {
        "status": status,
        "message": res.get("message", ""),
        "n": n,
        "elapsed_s": round(tiempo_s, 4),
        "determinant": det,
        "determinant_str": formatear_fraccion_str(det) if det is not None else None,
        "matrix_a": matriz_a,
        "matrix_a_latex": latex_a,
        "inverse": inversa,
        "inverse_latex": latex_inv,
        "steps": pasos_agrupados,
        "groups": grupos,
        "stats": stats,
        "verifications": verificaciones,
        "error_cell": None,
    }


class ControladorOperacionesInversas:
    """Gestiona el cálculo paso a paso de la matriz inversa para visualización didáctica."""

    @classmethod
    def procesar_inversa(cls, payload_json: str) -> dict:
        """Valida el payload y calcula la inversa paso a paso devolviendo un diccionario."""
        datos_crudos, err_json = parsear_payload(payload_json)
        if err_json is not None or datos_crudos is None:
            return construir_resultado_vacio("ERROR", "Payload JSON inválido.")

        matriz_a, n, error_resultado = validar_y_parsear_matriz_cuadrada(datos_crudos)
        if error_resultado is not None or matriz_a is None:
            return error_resultado or construir_resultado_vacio("ERROR", "Datos inválidos.")

        res, tiempo_s, err_ejecucion = _ejecutar_resolutor(matriz_a)
        if err_ejecucion is not None or res is None:
            return construir_resultado_vacio(
                "ERROR", err_ejecucion or "Error al resolver.", n=n, tiempo_s=tiempo_s, matriz_a=matriz_a
            )

        status = res.get("status", "ERROR")
        if status in ("ERROR", "SINGULAR"):
            det = res.get("determinant")
            return construir_resultado_vacio(
                status, res.get("message", "Error al resolver."), n=n, tiempo_s=tiempo_s, determinante=det, matriz_a=matriz_a
            )

        return _ensamblar_resultado_inversa(res, matriz_a, n, tiempo_s)

    @classmethod
    def construir_foco_paso(cls, pasos: list[dict], idx: int) -> dict:
        """Delega el cálculo de foco pedagógico al módulo especializado."""
        return construir_foco_paso(pasos, idx)
