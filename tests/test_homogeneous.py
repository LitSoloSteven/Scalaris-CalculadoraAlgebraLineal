"""Tests para solve_homogeneous.

Un sistema homogéneo Ax = 0 SIEMPRE tiene al menos la solución trivial
x = 0. La pregunta pedagógica es si además admite soluciones no triviales,
lo cual ocurre si y solo si rank(A) < n (número de variables).

Estados:
  - TRIVIAL_ONLY: rank(A) = n. Solo x = 0.
  - NON_TRIVIAL: rank(A) < n. Espacio solución de dimensión n - rank.
  - ERROR: input inválido.

Reutiliza GaussSolver internamente: construye [A | 0], pide la reducción
y extrae rank, pivot_cols, free_cols y la paramétrica.
"""
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.homogeneous import solve_homogeneous


# =========================================================================
# GRUPO 1 — Casos TRIVIAL_ONLY
# =========================================================================

class TestTrivialOnly:

    def test_identity_2x2(self):
        A = Matrix(2, 2, [[1, 0], [0, 1]])
        res = solve_homogeneous(A)
        assert res["status"] == "TRIVIAL_ONLY"
        assert res["rank"] == 2
        assert res["num_vars"] == 2
        assert res["free_cols"] == []
        assert res["solution_param"] is None

    def test_identity_3x3(self):
        A = Matrix(3, 3, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        res = solve_homogeneous(A)
        assert res["status"] == "TRIVIAL_ONLY"
        assert res["rank"] == 3

    def test_full_rank_2x2(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = solve_homogeneous(A)
        assert res["status"] == "TRIVIAL_ONLY"
        assert res["rank"] == 2
        assert res["free_cols"] == []

    def test_full_rank_3x3(self):
        A = Matrix(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
        res = solve_homogeneous(A)
        assert res["status"] == "TRIVIAL_ONLY"
        assert res["rank"] == 3

    def test_trivial_solution_is_zero_vector(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = solve_homogeneous(A)
        assert res["trivial_solution"] == [Fraction(0), Fraction(0)]

    def test_trivial_solution_3x3(self):
        A = Matrix(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
        res = solve_homogeneous(A)
        assert res["trivial_solution"] == [Fraction(0)] * 3


# =========================================================================
# GRUPO 2 — Casos NON_TRIVIAL
# =========================================================================

class TestNonTrivial:

    def test_zero_matrix_2x2(self):
        """Matriz nula: rank 0, todas las variables libres."""
        A = Matrix(2, 2, [[0, 0], [0, 0]])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 0
        assert res["free_cols"] == [0, 1]

    def test_single_dependent_row(self):
        """A = [[1, 2], [2, 4]]: rank 1, free_cols = [1]."""
        A = Matrix(2, 2, [[1, 2], [2, 4]])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 1
        assert res["free_cols"] == [1]

    def test_wide_matrix_1x3(self):
        """1×3: rank 1 < 3 → 2 variables libres."""
        A = Matrix(1, 3, [[1, 2, 3]])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 1
        assert res["free_cols"] == [1, 2]

    def test_dependent_columns_3x3(self):
        """A = [[1,2,3],[2,4,6],[3,6,9]]: rank 1, 2 libres."""
        A = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [3, 6, 9]])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 1
        assert res["free_cols"] == [1, 2]

    def test_rank_two_in_3x3(self):
        """A = [[1,0,1],[0,1,1],[0,0,0]]: rank 2, 1 libre."""
        A = Matrix(3, 3, [[1, 0, 1], [0, 1, 1], [0, 0, 0]])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 2
        assert res["free_cols"] == [2]

    def test_zero_matrix_3x3(self):
        A = Matrix(3, 3, [[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        res = solve_homogeneous(A)
        assert res["rank"] == 0
        assert res["free_cols"] == [0, 1, 2]

    def test_non_trivial_has_solution_param(self):
        A = Matrix(2, 2, [[1, 2], [2, 4]])
        res = solve_homogeneous(A)
        assert res["solution_param"] is not None
        assert res["solution_param"]["num_vars"] == 2
        assert res["solution_param"]["free_cols"] == [1]

    def test_solution_param_direction_in_kernel(self):
        """A·directions[k] == 0 con Fraction exacto."""
        A = Matrix(2, 2, [[1, 2], [2, 4]])
        res = solve_homogeneous(A)
        sp = res["solution_param"]
        for d in sp["directions"]:
            # A·d == 0
            lhs = sum(
                Fraction(A.get(0, j)) * d[j] for j in range(2)
            )
            assert lhs == Fraction(0), "A·d debe ser 0"

    def test_solution_param_particular_is_zero(self):
        """Para homogéneos, la particular siempre es 0."""
        A = Matrix(2, 2, [[1, 2], [2, 4]])
        res = solve_homogeneous(A)
        assert res["solution_param"]["particular"] == [Fraction(0), Fraction(0)]


# =========================================================================
# GRUPO 3 — Dimensiones y matrices rectangulares
# =========================================================================

class TestDimensions:

    def test_wide_matrix_3x5(self):
        """3×5 con rank 3: free_cols = [3, 4]."""
        A = Matrix(3, 5, [
            [1, 0, 0, 1, 2],
            [0, 1, 0, 3, 4],
            [0, 0, 1, 5, 6],
        ])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 3
        assert res["num_vars"] == 5
        assert res["free_cols"] == [3, 4]

    def test_tall_matrix_5x2_full_rank(self):
        """5×2 con rank 2: TRIVIAL_ONLY."""
        A = Matrix(5, 2, [
            [1, 0],
            [0, 1],
            [1, 1],
            [2, 1],
            [1, 2],
        ])
        res = solve_homogeneous(A)
        assert res["status"] == "TRIVIAL_ONLY"
        assert res["rank"] == 2
        assert res["free_cols"] == []

    def test_1x1_nonzero(self):
        A = Matrix(1, 1, [[5]])
        res = solve_homogeneous(A)
        assert res["status"] == "TRIVIAL_ONLY"
        assert res["rank"] == 1

    def test_1x1_zero(self):
        A = Matrix(1, 1, [[0]])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 0
        assert res["free_cols"] == [0]


# =========================================================================
# GRUPO 4 — Precisión con fracciones
# =========================================================================

class TestPrecision:

    def test_fractional_entries(self):
        A = Matrix(2, 2, [
            [Fraction(1, 2), Fraction(1, 3)],
            [Fraction(1, 4), Fraction(1, 5)],
        ])
        res = solve_homogeneous(A)
        # det = 1/60 ≠ 0 → TRIVIAL_ONLY
        assert res["status"] == "TRIVIAL_ONLY"
        assert res["rank"] == 2

    def test_fractional_dependent(self):
        """A = [[1/2, 1], [1/4, 1/2]]: segunda columna = 2 · primera."""
        A = Matrix(2, 2, [
            [Fraction(1, 2), Fraction(1)],
            [Fraction(1, 4), Fraction(1, 2)],
        ])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 1

    def test_large_denominator_does_not_truncate(self):
        """A = [[1001, 0], [1, 0]]: rank 1, free_cols = [1]."""
        A = Matrix(2, 2, [["1001", "0"], ["1", "0"]])
        res = solve_homogeneous(A)
        assert res["status"] == "NON_TRIVIAL"
        assert res["rank"] == 1
        assert res["free_cols"] == [1]


# =========================================================================
# GRUPO 5 — Validación
# =========================================================================

class TestValidation:

    def test_non_matrix_rejected(self):
        res = solve_homogeneous([[1, 2], [3, 4]])
        assert res["status"] == "ERROR"
        assert "Matrix" in res["message"]


# =========================================================================
# GRUPO 6 — Contrato
# =========================================================================

_EXPECTED_KEYS = {
    "status", "message", "rank", "num_vars",
    "pivot_cols", "free_cols", "trivial_solution",
    "solution_param", "reduced_matrix", "steps",
    "explanation", "error_cell",
}


class TestContract:

    def test_trivial_only_keys(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = solve_homogeneous(A)
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_non_trivial_keys(self):
        A = Matrix(2, 2, [[1, 2], [2, 4]])
        res = solve_homogeneous(A)
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_error_keys(self):
        res = solve_homogeneous([[1]])
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_does_not_mutate_input(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        snap = A.clone()
        solve_homogeneous(A)
        assert A == snap

    def test_explanation_present_trivial_only(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = solve_homogeneous(A)
        assert len(res["explanation"]) > 20
        assert "independiente" in res["explanation"].lower() or \
               "trivial" in res["explanation"].lower()

    def test_explanation_present_non_trivial(self):
        A = Matrix(2, 2, [[1, 2], [2, 4]])
        res = solve_homogeneous(A)
        assert len(res["explanation"]) > 20
        assert "dependiente" in res["explanation"].lower() or \
               "no trivial" in res["explanation"].lower()

    def test_explanation_mentions_rank_and_n(self):
        A = Matrix(2, 2, [[1, 2], [2, 4]])
        res = solve_homogeneous(A)
        assert "1" in res["explanation"]  # rank
        assert "2" in res["explanation"]  # num_vars

    def test_reduced_matrix_present_on_success(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = solve_homogeneous(A)
        assert res["reduced_matrix"] is not None
        assert res["reduced_matrix"].rows == 2
        assert res["reduced_matrix"].cols == 2

    def test_steps_present(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = solve_homogeneous(A)
        assert len(res["steps"]) > 0