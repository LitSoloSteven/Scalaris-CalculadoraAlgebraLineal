"""Sistemas homogéneos Ax = 0.

Un sistema homogéneo SIEMPRE tiene la solución trivial x = 0. La pregunta
pedagógica es si además admite soluciones no triviales:

  - rank(A) = n  → solo la trivial. Las columnas de A son linealmente
                   independientes.
  - rank(A) < n  → infinitas soluciones. El espacio solución tiene
                   dimensión n - rank y se parametriza con las variables
                   libres.

La prueba de independencia lineal de un conjunto de vectores
{v_1, ..., v_k} ⊂ R^n es exactamente este cálculo: los vectores son
linealmente independientes si y solo si el sistema homogéneo
[v_1 | ... | v_k] · c = 0 admite únicamente la solución trivial.

Reutilización:
  - Composición sobre GaussSolver. Se construye [A | 0] y se lee rank,
    free_cols, solution_param, echelon_matrix y steps. No se duplica la
    eliminación.
  - El último bloque de la respuesta (`explanation`) es texto en
    castellano ya formateado, pensado para que el frontend lo muestre
    directamente sin recomponer.
"""
from __future__ import annotations

from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.matrix_ops.formatters import matrix_to_latex


# =========================================================================
# API pública
# =========================================================================

def solve_homogeneous(matrix_a: Matrix) -> dict:
    """Clasifica un sistema homogéneo Ax = 0.

    Args:
        matrix_a: Matriz de coeficientes A (m×n).

    Returns:
        dict con:
          - status: TRIVIAL_ONLY | NON_TRIVIAL | ERROR
          - message: resumen de una línea, en castellano
          - rank: rango de A
          - num_vars: n (número de columnas de A)
          - pivot_cols: columnas con pivote
          - free_cols: columnas sin pivote (variables libres)
          - trivial_solution: [Fraction(0)] * n (x = 0 siempre es solución)
          - solution_param: dict | None (None si TRIVIAL_ONLY; ver
                            SolutionParam en gauss.py para el contrato)
          - reduced_matrix: A reducida por filas (m×n)
          - steps: pasos de la eliminación
          - explanation: str en castellano listo para mostrar
          - error_cell: None (reservado para futuras ampliaciones)
    """
    if not isinstance(matrix_a, Matrix):
        return _empty_result("ERROR", "Se esperaba una Matrix.")

    m, n = matrix_a.rows, matrix_a.cols

    # --- 1. Construir [A | 0] y reducir con GaussSolver ---
    augmented_data = []
    for i in range(m):
        row = [matrix_a.get(i, j) for j in range(n)]
        row.append(Fraction(0))
        augmented_data.append(row)
    augmented = Matrix(m, n + 1, augmented_data)

    gs = GaussSolver(augmented)
    result = gs.solve()

    free_cols = list(result.get("free_cols") or [])
    rank = n - len(free_cols)
    pivot_cols = [c for c in range(n) if c not in free_cols]

    # --- 2. Extraer A reducida (primeras n columnas del augmented reducido) ---
    reduced_aug = result["echelon_matrix"]
    reduced_data = [
        [reduced_aug.get(i, j) for j in range(n)]
        for i in range(m)
    ]
    reduced_a = Matrix(m, n, reduced_data)

    # --- 3. Formatear steps ---
    steps = _format_steps(result.get("steps", []))

    # --- 4. Clasificar ---
    trivial_solution = [Fraction(0)] * n

    if rank == n:
        return {
            "status": "TRIVIAL_ONLY",
            "message": (
                f"Sistema homogéneo con solución única: la trivial "
                f"(rank(A) = {rank} = n = {n})."
            ),
            "rank": rank,
            "num_vars": n,
            "pivot_cols": pivot_cols,
            "free_cols": [],
            "trivial_solution": trivial_solution,
            "solution_param": None,
            "reduced_matrix": reduced_a,
            "steps": steps,
            "explanation": (
                f"rank(A) = {rank} = número de variables ({n}). "
                f"Las columnas de A son linealmente independientes y el "
                f"sistema Ax = 0 admite únicamente la solución trivial x = 0."
            ),
            "error_cell": None,
        }

    # rank < n → NON_TRIVIAL
    dim = n - rank
    solution_param = result.get("solution_param")
    return {
        "status": "NON_TRIVIAL",
        "message": (
            f"Sistema homogéneo con infinitas soluciones: "
            f"rank(A) = {rank} < n = {n}. "
            f"Dimensión del espacio solución: {dim}."
        ),
        "rank": rank,
        "num_vars": n,
        "pivot_cols": pivot_cols,
        "free_cols": free_cols,
        "trivial_solution": trivial_solution,
        "solution_param": solution_param,
        "reduced_matrix": reduced_a,
        "steps": steps,
        "explanation": (
            f"rank(A) = {rank} < número de variables ({n}). "
            f"Las columnas de A son linealmente dependientes y el sistema "
            f"Ax = 0 admite soluciones no triviales: un espacio de "
            f"dimensión {dim} parametrizado por {dim} variable(s) libre(s)."
        ),
        "error_cell": None,
    }


# =========================================================================
# Helpers
# =========================================================================

def _empty_result(status: str, message: str) -> dict:
    return {
        "status": status,
        "message": message,
        "rank": None,
        "num_vars": None,
        "pivot_cols": [],
        "free_cols": [],
        "trivial_solution": [],
        "solution_param": None,
        "reduced_matrix": None,
        "steps": [],
        "explanation": "",
        "error_cell": None,
    }


def _format_steps(raw_steps: list[dict]) -> list[dict]:
    """Añade detail_latex a los steps de Gauss.

    No cambia la estructura original {description, matrix}; solo agrega
    detail_latex para que el frontend pueda renderizar cada paso sin
    reimplementar el formateador.
    """
    out = []
    for step in raw_steps:
        mat = step.get("matrix")
        out.append({
            "description": step["description"],
            "matrix": mat,
            "detail_latex": matrix_to_latex(mat) if mat is not None else None,
        })
    return out