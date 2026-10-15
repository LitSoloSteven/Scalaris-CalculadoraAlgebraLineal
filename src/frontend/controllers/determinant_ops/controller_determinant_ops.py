"""Controlador principal para el cálculo pedagógico de determinantes."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.backend.exceptions import AlgebraLinealError
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.determinants import (
    determinant_by_cofactors,
    determinant_by_lu,
    recommend_method,
)
from src.frontend.controllers._matriz_cuadrada import parsear_matriz_cuadrada
from src.frontend.controllers.determinant_ops._config import (
    COFACTORES_MAX_N,
    LU_MAX_N,
    METODOS,
)
from src.frontend.controllers.determinant_ops._foco import foco_paso
from src.frontend.controllers.determinant_ops._pasos_cofactores import (
    construir_pasos_cofactores,
)
from src.frontend.controllers.determinant_ops._pasos_lu import construir_pasos_lu
from src.frontend.controllers.determinant_ops._resultado import (
    armar_resultado,
    resultado_error,
)
from src.frontend.controllers.linear_systems._shared import parse_payload

logger = logging.getLogger(__name__)


def _extraer_mensaje_error_payload(err_json: Any) -> str:
    """Extrae el mensaje legible del error devuelto por parse_payload."""
    if isinstance(err_json, dict):
        return str(err_json.get("message", "Payload inválido."))
    if isinstance(err_json, str):
        try:
            err_dict = json.loads(err_json)
            if isinstance(err_dict, dict):
                return str(err_dict.get("message", "Payload inválido."))
        except Exception:
            return err_json
    return "Payload JSON inválido."


def _resolver(
    matriz: Matrix,
    metodo: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Ejecuta el solver del método elegido y construye sus pasos didácticos."""
    if metodo == "cofactores":
        res = determinant_by_cofactors(matriz)
        if res.get("status") != "SUCCESS":
            return res, [], [], {}
        pasos, grupos, stats = construir_pasos_cofactores(res, matriz.rows)
        return res, pasos, grupos, stats

    res = determinant_by_lu(matriz)
    if res.get("status") != "SUCCESS":
        return res, [], [], {}
    pasos, grupos, stats = construir_pasos_lu(res, matriz.rows)
    return res, pasos, grupos, stats


def _validar_metodo_y_limite(
    datos: dict[str, Any],
) -> tuple[str | None, int | None, str | None]:
    """Valida el método solicitado y verifica el límite de dimensión aplicable."""
    metodo_raw = datos.get("metodo", "cofactores")
    metodo = str(metodo_raw).strip() if isinstance(metodo_raw, str) else ""
    if metodo not in METODOS:
        return (
            None,
            None,
            "El método seleccionado no es válido. Elige Cofactores o Eliminación con pivoteo.",
        )

    n_val = datos.get("n")
    if (
        metodo == "cofactores"
        and isinstance(n_val, int)
        and not isinstance(n_val, bool)
        and n_val > COFACTORES_MAX_N
    ):
        return (
            metodo,
            None,
            f"La expansión por cofactores admite hasta {COFACTORES_MAX_N}×{COFACTORES_MAX_N}. "
            f"Usa eliminación con pivoteo para matrices más grandes.",
        )

    max_n = COFACTORES_MAX_N if metodo == "cofactores" else LU_MAX_N
    return metodo, max_n, None


class DeterminantOpsController:
    """Coordina la validación, resolución y estructuración de pasos de determinantes.

    Contrato del diccionario devuelto por `process_determinant(payload_json)`:
      - status: "SUCCESS" | "SINGULAR" | "ERROR"
      - message: str
      - n: int
      - metodo: "cofactores" | "lu" | ""
      - elapsed_s: float
      - determinante: Fraction | None
      - determinante_str: str | None
      - determinante_latex: str | None
      - es_singular: bool
      - matrix_a: Matrix | None
      - matrix_a_latex: str | None
      - steps: list[dict] con claves {index, kind, description, explanation,
        group_index, matrix, pivot, rows_changed, swap_rows, detail_latex, menor}
      - groups: list[dict] con claves {title, summary, kind, step_indices}
      - stats: dict con claves {total, pivotes, intercambios, eliminaciones,
        menores, terminos_cero}
      - swap_count: int
      - pivotes_str: list[str]
      - verifications: list[dict] con claves {key, title, coincide, detail_latex}
      - recomendacion: dict | None
      - error_cell: list[int] | None
    """

    @staticmethod
    def recomendar(n: int) -> dict[str, Any]:
        """Recomienda el método óptimo según la dimensión n."""
        return recommend_method(n)

    @staticmethod
    def build_focus_for_step(resultado: dict[str, Any], indice: int) -> dict[str, Any]:
        """Construye el recorte focal del paso indicado para el asistente Glosa."""
        if not isinstance(resultado, dict):
            return foco_paso([], indice, 0, "")
        pasos = resultado.get("steps") or []
        n = int(resultado.get("n") or 0)
        metodo = str(resultado.get("metodo") or "")
        return foco_paso(pasos, indice, n, metodo)

    @classmethod
    def process_determinant(cls, payload_json: str) -> dict[str, Any]:
        """Procesa una solicitud JSON de cálculo de determinante y devuelve el resultado."""
        inicio = time.perf_counter()
        try:
            datos, err_json = parse_payload(payload_json)
            if err_json is not None or not isinstance(datos, dict):
                msg = _extraer_mensaje_error_payload(err_json)
                return resultado_error(msg, elapsed_s=time.perf_counter() - inicio)

            metodo, max_n, err_metodo = _validar_metodo_y_limite(datos)
            if err_metodo is not None or metodo is None or max_n is None:
                n_raw = (
                    datos.get("n")
                    if isinstance(datos.get("n"), int) and not isinstance(datos.get("n"), bool)
                    else 0
                )
                return resultado_error(
                    err_metodo or "Método inválido.",
                    n=n_raw,
                    metodo=metodo or "",
                    elapsed_s=time.perf_counter() - inicio,
                )

            matriz, err_mat = parsear_matriz_cuadrada(datos, max_n=max_n)
            if err_mat is not None or matriz is None:
                return resultado_error(
                    err_mat["message"],
                    n=err_mat.get("n", 0),
                    metodo=metodo,
                    elapsed_s=time.perf_counter() - inicio,
                    error_cell=err_mat.get("error_cell"),
                )

            res_backend, pasos, grupos, stats = _resolver(matriz, metodo)
            if res_backend.get("status") != "SUCCESS":
                return resultado_error(
                    res_backend.get("message", "No se pudo calcular el determinante."),
                    n=matriz.rows,
                    metodo=metodo,
                    elapsed_s=time.perf_counter() - inicio,
                    matrix_a=matriz,
                )

            return armar_resultado(
                res_backend,
                pasos,
                grupos,
                stats,
                matriz=matriz,
                n=matriz.rows,
                metodo=metodo,
                elapsed_s=time.perf_counter() - inicio,
            )
        except (ValueError, AlgebraLinealError) as exc:
            return resultado_error(
                str(exc), elapsed_s=time.perf_counter() - inicio
            )
        except Exception:
            logger.exception("Error inesperado en process_determinant")
            return resultado_error(
                "Ocurrió un error inesperado al calcular el determinante. "
                "Revisa los datos e inténtalo de nuevo.",
                elapsed_s=time.perf_counter() - inicio,
            )