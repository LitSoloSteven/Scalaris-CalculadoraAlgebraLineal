"""Funciones para exportar cuadrículas de ecuaciones a representaciones algebraicas."""
from __future__ import annotations

from src.backend.utilidades.validadores import ValidadorMatriz


def _formatear_termino_variable(val: str, j: int, tiene_terminos: bool) -> str | None:
    """Convierte un coeficiente escalar en un termino con variable xj."""
    if not val or val == "0":
        return None
    valida, _, _ = ValidadorMatriz.parse_number_exact(val)
    if not valida:
        return None
    signo = "-" if val.startswith("-") else "+"
    val_abs = val.lstrip("+-").strip()
    coef = "" if val_abs == "1" or val_abs == "" else val_abs
    term = f"{coef}x{j+1}"
    if not tiene_terminos:
        return f"-{term}" if signo == "-" else term
    return f"{signo} {term}"


def exportar_ecuaciones_desde_datos(
    matriz_A: list[list[str]], vector_b: list[str], preserve_shape: bool
) -> list[str]:
    """Convierte los coeficientes de matriz y terminos independientes a texto de ecuaciones."""
    ecuaciones: list[str] = []
    for i, row in enumerate(matriz_A):
        terms = []
        for j, val in enumerate(row):
            term = _formatear_termino_variable(val, j, len(terms) > 0)
            if term:
                terms.append(term)

        b_val = vector_b[i] if i < len(vector_b) else "0"
        if not terms:
            cero_lado = "0x1" if preserve_shape else "0"
            ecuaciones.append(f"{cero_lado} = {b_val}" if (b_val and b_val != "0") else f"{cero_lado} = 0")
        else:
            ecuaciones.append(f"{' '.join(terms)} = {b_val}")
    return ecuaciones
