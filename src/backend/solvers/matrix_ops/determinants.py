"""Cálculo de determinantes por dos métodos pedagógicos.

  - determinant_by_cofactors: expansión recursiva por la primera fila,
    con traza de signos y menores. Inviable para n grande (O(n!)), se
    limita a COFACTOR_MAX_DIMENSION.

  - determinant_by_lu: eliminación con pivoteo parcial + producto de la
    diagonal × (-1)^swaps. Reutiliza GaussSolver como fuente única de
    verdad de la eliminación exacta. Complejidad O(n³) para matrices
    densas.

Ambos métodos devuelven el MISMO resultado exacto (Fraction) en casos
de referencia, y coinciden con MatrixOpsSolver.determinant, que usa una
eliminación a triangular superior sin traza pedagógica.

No se delega en ninguna biblioteca externa de álgebra lineal. Solo
stdlib + fractions.Fraction.
"""
from __future__ import annotations

from fractions import Fraction

from src.backend.constants import COFACTOR_MAX_DIMENSION
from src.backend.exceptions import DimensionMismatchError
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
from src.backend.utils.formatters import format_fraction_str, number_to_latex


# ---------------------------------------------------------------------------
# Umbral de recomendación.
# Por debajo de este n, la expansión por cofactores es comparable o más
# barata que LU (n=4: 24 ops por cofactores vs ~21 por LU). Por encima,
# el crecimiento factorial domina. Se documenta en el mensaje al usuario.
# ---------------------------------------------------------------------------
_RECOMMENDATION_THRESHOLD = 5


# ===========================================================================
# API pública
# ===========================================================================

def recommend_method(n: int) -> dict:
    """Recomienda método por tamaño sin bloquear la elección manual.

    Returns:
        dict con:
          - recommended: 'cofactores' o 'lu'
          - cofactor_complexity: 'O(n!) — crecimiento factorial'
          - lu_complexity: 'O(n³) para matrices densas'
          - reason: str con el motivo, en castellano, mencionando n
          - cofactor_available: False si n > COFACTOR_MAX_DIMENSION
    """
    if not isinstance(n, int) or n < 1:
        return {
            "recommended": "lu",
            "cofactor_complexity": "O(n!) — crecimiento factorial",
            "lu_complexity": "O(n³) para matrices densas",
            "reason": f"Dimensión inválida ({n!r}). Se sugiere LU por seguridad.",
            "cofactor_available": False,
        }

    cof_available = n <= COFACTOR_MAX_DIMENSION
    recommended = "cofactores" if (n < _RECOMMENDATION_THRESHOLD and cof_available) else "lu"

    if recommended == "cofactores":
        reason = (
            f"Para n={n}, la expansión por cofactores es perfectamente "
            f"viable y muestra cada signo y menor uno por uno. LU es más "
            f"eficiente a partir de n≈{_RECOMMENDATION_THRESHOLD}."
        )
    elif not cof_available:
        reason = (
            f"Para n={n}, la expansión por cofactores es inviable (n! "
            f"crece demasiado rápido). LU resuelve el determinante en "
            f"tiempo polinómico."
        )
    else:
        reason = (
            f"Para n={n}, LU es más eficiente: la expansión por cofactores "
            f"crece factorialmente y LU solo cúbicamente. Ambos dan el "
            f"mismo resultado exacto."
        )

    return {
        "recommended": recommended,
        "cofactor_complexity": "O(n!) — crecimiento factorial",
        "lu_complexity": "O(n³) para matrices densas",
        "reason": reason,
        "cofactor_available": cof_available,
    }


# ===========================================================================
# Expansión por cofactores
# ===========================================================================

def determinant_by_cofactors(matrix_a: Matrix) -> dict:
    """Determinante por expansión de cofactores con traza pedagógica."""
    if not isinstance(matrix_a, Matrix):
        return _empty_result(
            "ERROR",
            "Se esperaba una Matrix.",
            method="cofactores",
        )

    n_rows, n_cols = matrix_a.rows, matrix_a.cols
    if n_rows != n_cols:
        return _empty_result(
            "ERROR",
            f"El determinante solo está definido para matrices cuadradas "
            f"(recibido {n_rows}×{n_cols}).",
            method="cofactores",
        )

    if n_rows > COFACTOR_MAX_DIMENSION:
        return _empty_result(
            "ERROR",
            f"La expansión por cofactores excede el límite permitido "
            f"({COFACTOR_MAX_DIMENSION}). Use el método LU para esta matriz.",
            method="cofactores",
        )

    # Caso 1×1: no hay menores (serían 0×0) y el determinante es el único
    # elemento. Short-circuit antes de tocar la recursión.
    if n_rows == 1:
        det = Fraction(matrix_a.get(0, 0))
        return {
            "status": "SUCCESS",
            "message": "Determinante por cofactores calculado (1×1).",
            "method": "cofactores",
            "determinant": det,
            "determinant_str": format_fraction_str(det),
            "steps": [{
                "description": "Caso 1×1: el determinante es el único elemento.",
                "matrix": matrix_a.clone(),
                "detail_latex": f"\\det(A) = {number_to_latex(det)}",
            }],
            "minors": [],
            "swap_count": 0,
            "pivots": [],
            "error_cell": None,
        }

    det = _cofactor_recursive(matrix_a)
    minors = _build_top_level_minors(matrix_a)
    steps = _build_cofactor_steps(matrix_a, minors, det)

    det = _cofactor_recursive(matrix_a)
    minors = _build_top_level_minors(matrix_a)
    steps = _build_cofactor_steps(matrix_a, minors, det)

    return {
        "status": "SUCCESS",
        "message": f"Determinante por cofactores calculado ({n_rows}×{n_rows}).",
        "method": "cofactores",
        "determinant": det,
        "determinant_str": format_fraction_str(det),
        "steps": steps,
        "minors": minors,
        "swap_count": 0,
        "pivots": [],
        "error_cell": None,
    }


def _cofactor_recursive(m: Matrix) -> Fraction:
    """Recursión pura de expansión por la primera fila. Sin traza."""
    if m.rows == 1:
        return Fraction(m.get(0, 0))
    if m.rows == 2:
        return Fraction(m.get(0, 0)) * Fraction(m.get(1, 1)) - \
               Fraction(m.get(0, 1)) * Fraction(m.get(1, 0))

    total = Fraction(0)
    for j in range(m.cols):
        coeff = Fraction(m.get(0, j))
        if coeff == 0:
            continue
        minor = _minor_matrix(m, 0, j)
        sign = 1 if (0 + j) % 2 == 0 else -1
        total += sign * coeff * _cofactor_recursive(minor)
    return total


def _minor_matrix(m: Matrix, row: int, col: int) -> Matrix:
    """Devuelve la matriz que queda al eliminar fila y columna."""
    data = [
        [m.get(i, j) for j in range(m.cols) if j != col]
        for i in range(m.rows)
        if i != row
    ]
    return Matrix(m.rows - 1, m.cols - 1, data)


def _build_top_level_minors(m: Matrix) -> list[dict]:
    """Calcula cada menor de la primera fila y su signo."""
    minors = []
    for j in range(m.cols):
        minor = _minor_matrix(m, 0, j)
        minors.append({
            "row": 0,
            "col": j,
            "minor_matrix": minor,
            "value": _cofactor_recursive(minor),
            "sign": 1 if j % 2 == 0 else -1,
            "coeff": Fraction(m.get(0, j)),
        })
    return minors


def _build_cofactor_steps(m: Matrix, minors: list[dict], det: Fraction) -> list[dict]:
    """Genera la traza didáctica: fórmula + un paso por menor."""
    steps = []

    # Paso 1: patrón de signos y fórmula.
    terms_latex = []
    for j, minor in enumerate(minors):
        a = number_to_latex(minor["coeff"])
        m_tex = f"M_{{{1},{j + 1}}}"
        sign = "+" if minor["sign"] > 0 else "-"
        if j == 0:
            terms_latex.append(f"{a} \\cdot {m_tex}" if minor["sign"] > 0
                               else f"-{a} \\cdot {m_tex}")
        else:
            terms_latex.append(f"{sign} {a} \\cdot {m_tex}")

    formula_latex = (
        "\\det(A) = " + " ".join(terms_latex)
        + f" = {number_to_latex(det)}"
    )
    steps.append({
        "description": (
            f"Expansión por la primera fila. Signos alternados "
            f"(+ − + …) y cada M_1j es el menor que se obtiene al "
            f"eliminar la fila 1 y la columna j."
        ),
        "matrix": m.clone(),
        "detail_latex": formula_latex,
    })

    # Un paso por menor.
    for minor in minors:
        m_tex = matrix_to_latex(minor["minor_matrix"])
        val = number_to_latex(minor["value"])
        sign_str = "+" if minor["sign"] > 0 else "−"
        steps.append({
            "description": (
                f"Menor M_1{minor['col'] + 1}: eliminar fila 1 y columna "
                f"{minor['col'] + 1}. Signo {sign_str}."
            ),
            "matrix": minor["minor_matrix"],
            "detail_latex": (
                f"M_{{{1},{minor['col'] + 1}}} = {m_tex} "
                f"\\quad \\Rightarrow \\quad "
                f"\\det(M_{{{1},{minor['col'] + 1}}}) = {val}"
            ),
        })

    return steps


# ===========================================================================
# Método LU (pivoteo parcial + producto de diagonal)
# ===========================================================================

def determinant_by_lu(matrix_a: Matrix) -> dict:
    """Determinante por eliminación con pivoteo parcial + producto diagonal."""
    if not isinstance(matrix_a, Matrix):
        return _empty_result(
            "ERROR",
            "Se esperaba una Matrix.",
            method="lu",
        )

    n_rows, n_cols = matrix_a.rows, matrix_a.cols
    if n_rows != n_cols:
        return _empty_result(
            "ERROR",
            f"El determinante solo está definido para matrices cuadradas "
            f"(recibido {n_rows}×{n_cols}).",
            method="lu",
        )

    n = n_rows

    if n == 1:
        det = Fraction(matrix_a.get(0, 0))
        return {
            "status": "SUCCESS",
            "message": "Determinante por LU calculado (1×1).",
            "method": "lu",
            "determinant": det,
            "determinant_str": format_fraction_str(det),
            "steps": [{
                "description": "Caso 1×1: el determinante es el único elemento.",
                "matrix": matrix_a.clone(),
                "detail_latex": f"\\det(A) = {number_to_latex(det)}",
            }],
            "minors": [],
            "swap_count": 0,
            "pivots": [det],
            "error_cell": None,
        }

    # Construir [A | I_n] para reutilizar GaussSolver con num_rhs=n.
    augmented_data = []
    for i in range(n):
        row = [matrix_a.get(i, j) for j in range(n)]
        for j in range(n):
            row.append(Fraction(1) if i == j else Fraction(0))
        augmented_data.append(row)
    augmented = Matrix(n, 2 * n, augmented_data)

    gs = GaussSolver(
        augmented,
        num_rhs=n,
        pivot_strategy="partial",
        normalize_pivots=False,
    )
    reduction = gs.solve_reduction()

    rank = reduction["rank"]
    pivot_cols = reduction["pivot_cols"]
    reduced = reduction["reduced_matrix"]

    # Detectar singularidad: si rank < n, algún pivote es 0 → det = 0.
    if rank < n:
        det = Fraction(0)
        pivots = []
        steps = _build_lu_steps_singular(gs.steps, n, rank)
    else:
        pivots = [Fraction(reduced.get(i, pivot_cols[i])) for i in range(n)]
        sign = -1 if (gs.swap_count % 2) == 1 else 1
        product = Fraction(1)
        for p in pivots:
            product *= p
        det = Fraction(sign) * product
        steps = _build_lu_steps_regular(gs.steps, pivots, gs.swap_count, det)

    return {
        "status": "SUCCESS",
        "message": f"Determinante por LU calculado ({n}×{n}).",
        "method": "lu",
        "determinant": det,
        "determinant_str": format_fraction_str(det),
        "steps": steps,
        "minors": [],
        "swap_count": gs.swap_count,
        "pivots": pivots,
        "error_cell": None,
    }


def _build_lu_steps_regular(
    raw_steps: list[dict],
    pivots: list[Fraction],
    swaps: int,
    det: Fraction,
) -> list[dict]:
    """Traza LU: pasos de Gauss + paso final con producto de la diagonal."""
    out = []
    for i, step in enumerate(raw_steps):
        mat = step.get("matrix")
        out.append({
            "description": step["description"],
            "matrix": mat,
            "detail_latex": matrix_to_latex(mat) if mat is not None else None,
        })

    sign_str = "-1" if swaps % 2 == 1 else "1"
    pivots_str = " \\cdot ".join(number_to_latex(p) for p in pivots)
    final_latex = (
        f"\\det(A) = (-1)^{{{swaps}}} \\cdot "
        f"\\prod_{{i=1}}^{{{len(pivots)}}} u_{{ii}} = "
        f"({sign_str}) \\cdot \\left( {pivots_str} \\right) = "
        f"{number_to_latex(det)}"
    )
    out.append({
        "description": (
            f"Producto de la diagonal de U por (-1)^({swaps} swaps): "
            f"det(A) = {format_fraction_str(det)}."
        ),
        "matrix": None,
        "detail_latex": final_latex,
    })
    return out


def _build_lu_steps_singular(
    raw_steps: list[dict],
    n: int,
    rank: int,
) -> list[dict]:
    """Traza LU cuando A es singular: sin producto, con mensaje explícito."""
    out = []
    for step in raw_steps:
        mat = step.get("matrix")
        out.append({
            "description": step["description"],
            "matrix": mat,
            "detail_latex": matrix_to_latex(mat) if mat is not None else None,
        })
    out.append({
        "description": (
            f"A es singular (rank={rank} < {n}). Un pivote de la diagonal "
            f"es cero, por lo tanto det(A) = 0."
        ),
        "matrix": None,
        "detail_latex": r"\det(A) = 0",
    })
    return out


# ===========================================================================
# Helpers
# ===========================================================================

def _empty_result(status: str, message: str, *, method: str) -> dict:
    return {
        "status": status,
        "message": message,
        "method": method,
        "determinant": None,
        "determinant_str": None,
        "steps": [],
        "minors": [],
        "swap_count": 0,
        "pivots": [],
        "error_cell": None,
    }