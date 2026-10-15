"""Construcción del foco de paso para que Glosa explique sin recalcular."""
from __future__ import annotations

from typing import Any

from src.ai.context import compact_number, excerpt_rows, sanitize_user_string
from src.backend.utils.formatters import format_fraction_str

LIMITE_TEXTO_DETALLE = 64


def _foco_vacio(detalle: dict[str, Any] | None = None) -> dict[str, Any]:
    """Devuelve la estructura de foco vacía."""
    return {
        "rows_before": {},
        "rows_after": {},
        "cols": None,
        "detail": detalle if detalle is not None else {},
    }


def _recortar_matriz_a_n(matriz: Any, n: int) -> list[list[str]]:
    """Extrae las primeras n columnas de una Matrix como textos exactos."""
    if matriz is None or not hasattr(matriz, "rows") or not hasattr(matriz, "cols"):
        return []
    limite_cols = min(n, matriz.cols)
    return [
        [format_fraction_str(matriz.get(f, c)) for c in range(limite_cols)]
        for f in range(matriz.rows)
    ]


def _contar_intercambios_hasta(pasos: list[dict[str, Any]], indice_tope: int) -> int:
    """Cuenta cuántos pasos de intercambio ocurrieron hasta indice_tope inclusive."""
    return sum(
        1
        for p in pasos[: indice_tope + 1]
        if p.get("kind") == "intercambio"
    )


def _filas_objetivo_lu(paso: dict[str, Any]) -> tuple[list[int], int]:
    """Determina los índices de fila relevantes y la columna central para LU."""
    swap = paso.get("swap_rows")
    if swap:
        return list(swap), 0
    cambiadas = paso.get("rows_changed")
    pivote = paso.get("pivot")
    col_central = int(pivote[1]) if pivote and len(pivote) >= 2 else 0
    if cambiadas:
        return list(cambiadas), col_central
    if pivote and len(pivote) >= 1:
        return [int(pivote[0])], col_central
    return [0], 0


def _foco_lu(
    pasos: list[dict[str, Any]],
    indice: int,
    n: int,
) -> dict[str, Any]:
    """Construye el foco para un paso del método de eliminación con pivoteo (LU)."""
    paso = pasos[indice]
    kind = paso.get("kind", "")

    if kind in ("producto", "singular"):
        intercambios = _contar_intercambios_hasta(pasos, indice)
        return _foco_vacio({"intercambios": intercambios})

    mat_actual = paso.get("matrix")
    if mat_actual is None:
        return _foco_vacio()

    mat_previa = pasos[indice - 1].get("matrix") if indice > 0 else mat_actual
    if mat_previa is None:
        mat_previa = mat_actual

    filas_idx, col_central = _filas_objetivo_lu(paso)
    datos_antes = _recortar_matriz_a_n(mat_previa, n)
    datos_despues = _recortar_matriz_a_n(mat_actual, n)

    rows_before, cols_before = excerpt_rows(datos_antes, filas_idx, col_central)
    rows_after, cols_after = excerpt_rows(datos_despues, filas_idx, col_central)
    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "cols": cols_after or cols_before,
        "detail": {},
    }


def _foco_cofactores(
    paso: dict[str, Any],
    n: int,
) -> dict[str, Any]:
    """Construye el foco para un paso de expansión por cofactores."""
    if paso.get("kind") != "menor":
        return _foco_vacio()

    menor = paso.get("menor")
    mat = paso.get("matrix")
    if not isinstance(menor, dict) or mat is None:
        return _foco_vacio()

    limite_cols = min(n, getattr(mat, "cols", 0))
    fila_uno = [
        compact_number(format_fraction_str(mat.get(0, c)))
        for c in range(limite_cols)
    ]
    signo_str = "+" if int(menor.get("signo", 1)) >= 0 else "-"
    coef_str = sanitize_user_string(
        str(menor.get("coeficiente_str", "0")), LIMITE_TEXTO_DETALLE
    )
    valor_str = sanitize_user_string(
        str(menor.get("valor_str", "0")), LIMITE_TEXTO_DETALLE
    )

    return {
        "rows_before": {"1": fila_uno} if fila_uno else {},
        "rows_after": {},
        "cols": None,
        "detail": {
            "signo": signo_str,
            "coeficiente": coef_str,
            "valor_menor": valor_str,
        },
    }


def foco_paso(
    pasos: list[dict[str, Any]],
    indice: int,
    n: int,
    metodo: str,
) -> dict[str, Any]:
    """Devuelve rows_before, rows_after, cols y detail para el paso indicado."""
    if not isinstance(pasos, list) or not (0 <= indice < len(pasos)):
        return _foco_vacio()

    paso = pasos[indice]
    if not isinstance(paso, dict):
        return _foco_vacio()

    if metodo == "cofactores":
        return _foco_cofactores(paso, n)
    if metodo == "lu":
        return _foco_lu(pasos, indice, n)
    return _foco_vacio()