"""Cálculo de foco visual (filas antes/después y columnas) para un paso del reproductor."""
from typing import Any

from src.ai.contexto import extraer_filas
from src.frontend.controladores.clasificador_pasos import clasificar_paso


def _obtener_filas_de_matriz(matriz: Any) -> list[list]:
    """Extrae las filas completas de una matriz como lista de fracciones o valores."""
    cantidad_columnas = getattr(matriz, "columnas", getattr(matriz, "cols", 0))
    cantidad_filas = getattr(matriz, "filas", getattr(matriz, "rows", 0))
    return [
        [matriz.obtener(r, c) if hasattr(matriz, "obtener") else matriz.get(r, c) for c in range(cantidad_columnas)]
        for r in range(cantidad_filas)
    ]


def _determinar_columna_central(pasos: list[dict], idx: int, parsed: dict) -> int:
    """Identifica la columna sobre la cual recae el pivote o la operación del paso."""
    paso = pasos[idx]
    if paso.get("pivot"):
        return paso["pivot"][1]
    if parsed.get("col") is not None:
        return parsed["col"]
    for k in range(idx, -1, -1):
        if pasos[k].get("pivot"):
            return pasos[k]["pivot"][1]
    return 0


def _determinar_indices_foco(kind: str, parsed: dict, paso: dict) -> tuple[list[int], list[int]]:
    """Calcula las listas de índices antes y después de la operación elemental."""
    r1, r2 = parsed.get("row1"), parsed.get("row2")
    if kind == "intercambio":
        swap = paso.get("swap_rows") if (r1 is None or r2 is None) else None
        f1, f2 = (swap[0], swap[1]) if swap else (r1, r2)
        indices = [f1, f2] if f1 is not None and f2 is not None else []
        return indices, indices
    if kind == "eliminacion":
        destino = [r1] if r1 is not None else paso.get("rows_changed", [0])
        origen = [r2] if (r2 is not None and r2 not in destino) else []
        return destino + origen, destino
    if kind in ("normalizacion", "pivote"):
        cambio = paso.get("rows_changed", [0])
        piv = paso.get("pivot", [0])
        r = r1 if r1 is not None else (cambio[0] if cambio else (piv[0] if piv else 0))
        return [r], [r]
    objetivo = list(paso.get("rows_changed", [])) or ([paso["pivot"][0]] if paso.get("pivot") else [0])
    return objetivo, objetivo


def _extraer_foco_por_tipo(
    parsed: dict,
    paso: dict,
    filas_previas: list,
    filas_actuales: list,
    col_centro: int,
) -> tuple[dict, dict, list | None]:
    """Obtiene el extracto de filas afectadas según la clase de operación."""
    kind = parsed.get("kind", paso.get("kind", "otro"))
    idx_antes, idx_despues = _determinar_indices_foco(kind, parsed, paso)
    if not idx_antes and not idx_despues:
        return {}, {}, None
    antes, columnas_foco = extraer_filas(filas_previas, idx_antes, col_centro)
    despues, _ = extraer_filas(filas_actuales, idx_despues, col_centro)
    return antes, despues, columnas_foco


def construir_foco_paso(pasos: list[dict], idx: int) -> dict:
    """Calcula rows_before, rows_after y cols para enfocar pedagógicamente un paso."""
    if not pasos:
        return {"rows_before": {}, "rows_after": {}, "cols": None}

    i = idx if (0 <= idx < len(pasos)) else (idx - 1 if 1 <= idx <= len(pasos) else max(0, min(idx, len(pasos) - 1)))
    paso = pasos[i]
    mat = paso.get("matrix")
    if mat is None:
        return {"rows_before": {}, "rows_after": {}, "cols": None}

    filas = _obtener_filas_de_matriz(mat)
    mat_prev = pasos[i - 1].get("matrix", mat) if i > 0 else mat
    filas_prev = _obtener_filas_de_matriz(mat_prev) if mat_prev else filas

    parsed = clasificar_paso(paso.get("description", ""))
    col_centro = _determinar_columna_central(pasos, i, parsed)

    antes, despues, columnas_foco = _extraer_foco_por_tipo(
        parsed, paso, filas_prev, filas, col_centro
    )
    return {"rows_before": antes, "rows_after": despues, "cols": columnas_foco}
