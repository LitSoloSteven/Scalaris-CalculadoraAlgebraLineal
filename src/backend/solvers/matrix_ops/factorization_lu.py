"""Factorización A = LU sin pivoteo.

Descompone una matriz A (m×n) en L (m×m unitaria triangular inferior) y
U (m×n escalonada) tales que A = L·U.

Restricciones algebraicas (PPT Factorización LU):
  - No se permite intercambiar filas. Si aparece un pivote cero, se
    devuelve status='NEEDS_PIVOTING' con la coordenada del pivote. La
    variante con permutaciones es PA = LU, otra feature.
  - El pre-check det(A) = 0 solo aplica cuando m == n. En rectangulares
    no existe determinante y la defensa queda en la detección de pivote
    cero durante la eliminación.

Reutilización:
  - Composición sobre GaussSolver con capture_multipliers=True y
    pivot_strategy='none'. El solver de Gauss sigue siendo la fuente
    única de verdad de la eliminación exacta. Aquí solo se leen los
    multiplicadores que ya calcula y se reordenan como L.
  - U sale de las primeras n columnas de la matriz reducida de [A | I_m]
    (con num_rhs=m). El bloque identidad que se añade a la derecha se
    ignora: es solo el truco para reutilizar GaussSolver sin tocar su
    validación de num_rhs.

Verificación final: A == L·U con Fraction exacto (nada de tolerancias
numéricas), con su paso correspondiente en `steps`.
"""
from __future__ import annotations

from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver


class LUFactorizationSolver:
    """Calcula A = L·U sin pivoteo, con verificación exacta."""

    def __init__(self):
        self.ops_solver = MatrixOpsSolver()

    # ------------------------------------------------------------------
    # Constructores de respuesta
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_result(status: str, message: str, *, error_cell=None) -> dict:
        return {
            "status": status,
            "message": message,
            "L": None,
            "U": None,
            "L_latex": None,
            "U_latex": None,
            "steps": [],
            "multipliers": [],
            "verification": None,
            "error_cell": error_cell,
        }

    # ------------------------------------------------------------------
    # Núcleo
    # ------------------------------------------------------------------

    def solve(self, matrix_a: Matrix) -> dict:
        # --- 1. Validación básica ---
        if not isinstance(matrix_a, Matrix):
            return self._empty_result(
                "ERROR",
                "Se esperaba una Matrix.",
            )

        m, n = matrix_a.rows, matrix_a.cols

        # --- 2. Pre-check det(A) = 0 para cuadradas ---
        if m == n:
            det = self.ops_solver.determinant(matrix_a)
            if det == 0:
                return self._empty_result(
                    "SINGULAR",
                    "det(A) = 0. A es singular; A = LU no existe.",
                )

        # --- 3. Construir [A | I_m] para reutilizar GaussSolver ---
        # El bloque identidad es un truco para que GaussSolver reciba un
        # "sistema" con num_rhs=m, pero solo leemos las primeras n
        # columnas de la matriz reducida (que corresponden a U).
        augmented_data = []
        for i in range(m):
            row = [matrix_a.get(i, j) for j in range(n)]
            for j in range(m):
                row.append(Fraction(1) if i == j else Fraction(0))
            augmented_data.append(row)
        augmented = Matrix(m, n + m, augmented_data)

        # --- 4. Eliminación sin pivoteo con captura de multiplicadores ---
        gs = GaussSolver(
            augmented,
            num_rhs=m,
            capture_multipliers=True,
            pivot_strategy="none",
            normalize_pivots=False,
        )
        reduction = gs.solve_reduction()

        # --- 5. Detección de pivote cero ---
        if gs.zero_pivots:
            first_col = gs.zero_pivots[0]
            # El pivote cero ocurrió en la fila = cantidad de pivotes
            # encontrados en columnas anteriores a first_col. No usamos
            # reduction["rank"] porque ese es el total de pivotes al
            # final, no la fila donde se encontró el cero.
            pivot_row_at_skip = sum(
                1 for c in reduction["pivot_cols"] if c < first_col
            )
            return self._empty_result(
                "NEEDS_PIVOTING",
                (
                    f"Pivote cero en la columna {first_col + 1} (fila "
                    f"{pivot_row_at_skip + 1}) sin posibilidad de intercambio. "
                    f"Se requiere la factorización PA = LU."
                ),
                error_cell=[pivot_row_at_skip, first_col],
            )

        # --- 6. Extraer U (primeras n columnas de la reducida) ---
        reduced = reduction["reduced_matrix"]
        U_data = [
            [reduced.get(i, j) for j in range(n)]
            for i in range(m)
        ]
        U = Matrix(m, n, U_data)

        # --- 7. Construir L (m×m unitaria triangular inferior) ---
        L_data = [
            [Fraction(1) if i == j else Fraction(0) for j in range(m)]
            for i in range(m)
        ]
        for mult in gs.multipliers:
            L_data[mult["row"]][mult["col"]] = mult["value"]
        L = Matrix(m, m, L_data)

        # --- 8. Formatear steps + agregar paso de verificación ---
        steps = self._format_steps(gs.steps, m, n)
        verification_step = self._build_verification_step(
            matrix_a, L, U, m, n,
        )
        steps.append(verification_step)

        # --- 9. Armar respuesta ---
        return {
            "status": "SUCCESS",
            "message": f"Factorización A = LU completada ({m}×{n}).",
            "L": L,
            "U": U,
            "L_latex": matrix_to_latex(L),
            "U_latex": matrix_to_latex(U),
            "steps": steps,
            "multipliers": list(gs.multipliers),
            "verification": {
                "coincide": verification_step["coincide"],
                "detail_latex": verification_step["detail_latex"],
            },
            "error_cell": None,
        }

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _format_steps(raw_steps: list[dict], m: int, n: int) -> list[dict]:
        """Convierte los steps de Gauss ({description, matrix}) al formato
        moderno con `detail_latex`, y reescribe el primer paso de [A|b]
        a [A|I] porque el bloque aumentado es la identidad."""
        out = []
        for i, step in enumerate(raw_steps):
            mat = step.get("matrix")
            description = step["description"]
            if i == 0 and "[A|b]" in description:
                description = description.replace("[A|b]", "[A|I]")
            detail_latex = None
            if mat is not None:
                # matrix_to_latex no maneja el bloque particionado; usamos
                # bmatrix simple sobre la matriz completa. La vista puede
                # decidir la partición.
                detail_latex = matrix_to_latex(mat)
            out.append({
                "description": description,
                "matrix": mat,
                "detail_latex": detail_latex,
            })
        return out

    def _build_verification_step(
        self, A: Matrix, L: Matrix, U: Matrix, m: int, n: int,
    ) -> dict:
        """Verifica A == L·U con Fraction exacto y devuelve el paso final."""
        product = self.ops_solver.multiply(L, U)["result_matrix"]
        coincide = all(
            product.get(i, j) == A.get(i, j)
            for i in range(m)
            for j in range(n)
        )
        status_word = "Correcto" if coincide else "Incorrecto"
        detail_latex = (
            f"L \\cdot U = {matrix_to_latex(product)}"
            f" \\quad (\\text{{{status_word}}})"
        )
        return {
            "description": f"Verificación A = L·U ({status_word}).",
            "matrix": product,
            "detail_latex": detail_latex,
            "coincide": coincide,
        }