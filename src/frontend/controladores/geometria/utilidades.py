"""Utilidades de detección de errores de entrada y formateo para visualización geométrica."""
from fractions import Fraction

from src.backend.utilidades.validadores import ValidadorMatriz


def selector_celda_error(
    celda_error: dict,
    *,
    escena: str = "",
    n_cuadricula: int = 0,
) -> str | None:
    """Genera el selector CSS para enfocar la celda inválida en la interfaz."""
    if not celda_error:
        return None
    n = n_cuadricula
    tipo = celda_error.get("kind")
    if tipo == "A":
        fila = celda_error.get("row", 0)
        col = celda_error.get("col", 0)
        return f'input[data-row="{fila}"][data-col="{col}"]'
    if tipo == "b":
        fila = celda_error.get("row", 0)
        return f'input[data-row="{fila}"][data-col="{n}"]'
    if tipo == "vec":
        nombre = celda_error.get("name", "")
        indice = celda_error.get("index", 0)
        panel_id = "geometria_vectores" if escena == "vectores" else "geometria_combinacion"
        return f'input[data-geometria-vector="{panel_id}_{nombre}"][data-geometria-indice="{indice}"]'
    return None


def ubicar_error_celda(matriz_a_cruda: list, vector_b_crudo: list) -> dict | None:
    """Escanea las celdas del sistema e identifica la primera coordenada con valor inválido."""
    for i, fila in enumerate(matriz_a_cruda):
        for j, celda in enumerate(fila):
            texto = str(celda).strip() if celda is not None and str(celda).strip() else "0"
            ok, _, _ = ValidadorMatriz.parsear_numero_exacto(texto)
            if not ok:
                return {"kind": "A", "row": i, "col": j}
    for i, celda in enumerate(vector_b_crudo):
        texto = str(celda).strip() if celda is not None and str(celda).strip() else "0"
        ok, _, _ = ValidadorMatriz.parsear_numero_exacto(texto)
        if not ok:
            return {"kind": "b", "row": i}
    return None


def ubicar_error_vector(vectores_crudos: list[list[str]], nombres: list[str]) -> dict | None:
    """Escanea los vectores e identifica el nombre e índice de la primera celda inválida."""
    for vi, vec in enumerate(vectores_crudos):
        for ci, celda in enumerate(vec):
            texto = str(celda).strip() if celda is not None and str(celda).strip() else "0"
            ok, _, _ = ValidadorMatriz.parsear_numero_exacto(texto)
            if not ok:
                return {"kind": "vec", "name": nombres[vi], "index": ci}
    return None


def a_flotante_seguro(valor: Fraction) -> float | None:
    """Convierte una fracción a flotante capturando desbordamientos."""
    try:
        return float(valor)
    except (OverflowError, ValueError):
        return None
