"""Ensamblado del diccionario de respuesta del controlador de determinantes.

Claves del diccionario devuelto por `armar_resultado` y `resultado_error`:
  - status: "SUCCESS" | "SINGULAR" | "ERROR" (SINGULAR cuando det == 0)
  - message: str (mensaje principal en español)
  - n: int (dimensión de la matriz cuadrada)
  - metodo: str ("cofactores" | "lu" | "")
  - elapsed_s: float (tiempo de cómputo redondeado a 4 decimales)
  - determinante: Fraction | None
  - determinante_str: str | None
  - determinante_latex: str | None
  - es_singular: bool
  - matrix_a: Matrix | None
  - matrix_a_latex: str | None (con vmatrix si n <= LATEX_MAX_N, si no None)
  - steps: list[dict]
  - groups: list[dict]
  - stats: dict
  - swap_count: int
  - pivotes_str: list[str]
  - verifications: list[dict] (cada elemento con key, title, coincide, detail_latex)
  - recomendacion: dict | None
  - error_cell: list[int] | None
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.determinants import recommend_method
from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.frontend.controllers.determinant_ops._config import LATEX_MAX_N

DECIMALES_TIEMPO = 4


def _matriz_a_vmatrix_latex(matriz: Matrix | None, n: int) -> str | None:
    """Renderiza la matriz en entorno vmatrix si n <= LATEX_MAX_N."""
    if matriz is None or n < 1 or n > LATEX_MAX_N:
        return None
    latex_base = matrix_to_latex(matriz)
    return (
        latex_base.replace(r"\begin{bmatrix}", r"\begin{vmatrix}")
        .replace(r"\end{bmatrix}", r"\end{vmatrix}")
    )


def _construir_verificacion_cruzada(
    matriz: Matrix,
    determinante: Fraction,
) -> dict[str, Any]:
    """Verifica el determinante contra MatrixOpsSolver.determinant."""
    det_independiente = MatrixOpsSolver().determinant(matriz)
    coincide = det_independiente == determinante
    estado_tex = "Correcto" if coincide else "Incorrecto"
    det_tex = number_to_latex(det_independiente)
    return {
        "key": "cruzada",
        "title": "Verificación independiente (aritmética exacta)",
        "coincide": coincide,
        "detail_latex": f"\\det(A) = {det_tex} \\quad (\\text{{{estado_tex}}})",
    }


def _construir_verificacion_terminos(
    minors: list[dict[str, Any]],
    determinante: Fraction,
) -> dict[str, Any]:
    """Verifica que la suma de signo * coeficiente * menor coincida con det(A)."""
    suma = Fraction(0)
    terminos_tex: list[str] = []

    for idx, minor in enumerate(minors):
        signo = Fraction(int(minor.get("sign", 1)))
        coef = Fraction(minor.get("coeff", 0))
        valor = Fraction(minor.get("value", 0))
        aporte = signo * coef * valor
        suma += aporte

        if aporte == 0:
            terminos_tex.append("0" if idx == 0 else "+ 0")
        elif idx == 0:
            terminos_tex.append(number_to_latex(aporte))
        elif aporte > 0:
            terminos_tex.append(f"+ {number_to_latex(aporte)}")
        else:
            terminos_tex.append(f"- {number_to_latex(abs(aporte))}")

    coincide = suma == determinante
    estado_tex = "Correcto" if coincide else "Incorrecto"
    cuerpo_suma = " ".join(terminos_tex) if terminos_tex else "0"
    return {
        "key": "terminos",
        "title": "La suma de los términos es det(A)",
        "coincide": coincide,
        "detail_latex": (
            f"{cuerpo_suma} = {number_to_latex(suma)} "
            f"\\quad (\\text{{{estado_tex}}})"
        ),
    }


def resultado_error(
    message: str,
    *,
    n: int = 0,
    metodo: str = "",
    elapsed_s: float = 0.0,
    matrix_a: Matrix | None = None,
    error_cell: list[int] | None = None,
) -> dict[str, Any]:
    """Construye un diccionario homogéneo con estado ERROR."""
    return {
        "status": "ERROR",
        "message": message,
        "n": n,
        "metodo": metodo,
        "elapsed_s": round(float(elapsed_s), DECIMALES_TIEMPO),
        "determinante": None,
        "determinante_str": None,
        "determinante_latex": None,
        "es_singular": False,
        "matrix_a": matrix_a,
        "matrix_a_latex": _matriz_a_vmatrix_latex(matrix_a, n),
        "steps": [],
        "groups": [],
        "stats": {},
        "swap_count": 0,
        "pivotes_str": [],
        "verifications": [],
        "recomendacion": recommend_method(n) if isinstance(n, int) and n >= 1 else None,
        "error_cell": error_cell,
    }


def armar_resultado(
    respuesta_backend: dict[str, Any],
    pasos: list[dict[str, Any]],
    grupos: list[dict[str, Any]],
    stats: dict[str, int],
    *,
    matriz: Matrix,
    n: int,
    metodo: str,
    elapsed_s: float,
) -> dict[str, Any]:
    """Ensambla el diccionario final de éxito o singularidad para la vista."""
    det = Fraction(respuesta_backend.get("determinant", 0))
    es_singular = det == 0
    status = "SINGULAR" if es_singular else "SUCCESS"
    mensaje = (
        "El determinante es 0: la matriz es singular y no tiene inversa."
        if es_singular
        else "Determinante calculado: la matriz es invertible (det ≠ 0)."
    )

    verificaciones = [_construir_verificacion_cruzada(matriz, det)]
    if metodo == "cofactores":
        minors = respuesta_backend.get("minors") or []
        verificaciones.append(_construir_verificacion_terminos(minors, det))

    pivotes_raw = respuesta_backend.get("pivots") or []
    pivotes_str = [format_fraction_str(Fraction(p)) for p in pivotes_raw]

    return {
        "status": status,
        "message": mensaje,
        "n": n,
        "metodo": metodo,
        "elapsed_s": round(float(elapsed_s), DECIMALES_TIEMPO),
        "determinante": det,
        "determinante_str": format_fraction_str(det),
        "determinante_latex": number_to_latex(det),
        "es_singular": es_singular,
        "matrix_a": matriz,
        "matrix_a_latex": _matriz_a_vmatrix_latex(matriz, n),
        "steps": pasos,
        "groups": grupos,
        "stats": stats,
        "swap_count": int(respuesta_backend.get("swap_count", 0)),
        "pivotes_str": pivotes_str,
        "verifications": verificaciones,
        "recomendacion": recommend_method(n),
        "error_cell": None,
    }