"""Tests para solve_leontief.

Cubre:
- Casos canónicos con solución única (trivial, diagonal, 2×2 acoplado, 3×3).
- Preservación de precisión exacta (Fraction, denominadores > 1000).
- Verificación (I − A)·x == d con Fraction exacto.
- Estados NO_SOLUTION / INFINITE_SOLUTIONS.
- Validación de inputs (no Matrix, no cuadrada, dims incompatibles, sector_names).
- Contrato: claves exactas, no mutación, interpretación no vacía.
- sector_names: default x_1..x_n y custom. Si se elimina la funcionalidad,
  estos tests se borran sin afectar al resto.
"""
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.leontief import solve_leontief


# =========================================================================
# GRUPO 1 — Casos SUCCESS básicos
# =========================================================================

class TestSuccessBasics:

    def test_1x1_zero_A(self):
        """A = [[0]], d = [[5]] → x = [5]."""
        A = Matrix(1, 1, [[0]])
        d = Matrix(1, 1, [[5]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"] == [Fraction(5)]

    def test_2x2_zero_A(self):
        """A = 0, d = [1, 2] → x = [1, 2] (x = d)."""
        A = Matrix(2, 2, [[0, 0], [0, 0]])
        d = Matrix(2, 1, [[1], [2]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"] == [Fraction(1), Fraction(2)]

    def test_2x2_diagonal_A(self):
        """A = diag(1/2, 1/4), d = [2, 3] → (I-A) = diag(1/2, 3/4) → x = [4, 4]."""
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"] == [Fraction(4), Fraction(4)]

    def test_2x2_coupled_A(self):
        """A = [[1/2, 1/4], [1/4, 1/2]], d = [1, 1].
        I - A = [[1/2, -1/4], [-1/4, 1/2]], det = 3/16.
        (I-A)^-1 = (16/3)·[[1/2, 1/4], [1/4, 1/2]] → x = [4, 4]."""
        A = Matrix(2, 2, [[Fraction(1, 2), Fraction(1, 4)],
                          [Fraction(1, 4), Fraction(1, 2)]])
        d = Matrix(2, 1, [[1], [1]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"] == [Fraction(4), Fraction(4)]

    def test_3x3_diagonal(self):
        """3 sectores con A diagonal: x = [2, 3, 4]."""
        A = Matrix(3, 3, [
            [Fraction(1, 2), 0, 0],
            [0, Fraction(2, 3), 0],
            [0, 0, Fraction(3, 4)],
        ])
        d = Matrix(3, 1, [[1], [1], [1]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"] == [Fraction(2), Fraction(3), Fraction(4)]


# =========================================================================
# GRUPO 2 — Precisión exacta
# =========================================================================

class TestPrecision:

    def test_preserves_large_denominator(self):
        """A = diag(1000/1001, 0), d = [1, 0] → x = [1001, 0]."""
        A = Matrix(2, 2, [[Fraction(1000, 1001), 0], [0, 0]])
        d = Matrix(2, 1, [[1], [0]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"][0] == Fraction(1001)
        assert res["x"][1] == Fraction(0)

    def test_fractional_solution_not_truncated(self):
        """A = [[2/3]], d = [[1]] → (I-A) = [[1/3]] → x = [3]."""
        A = Matrix(1, 1, [[Fraction(2, 3)]])
        d = Matrix(1, 1, [[1]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"] == [Fraction(3)]

    def test_fractional_solution_denominator_above_1000(self):
        """A = [[1000/1001]], d = [[1]] → (I-A) = [[1/1001]] → x = [1001]."""
        A = Matrix(1, 1, [[Fraction(1000, 1001)]])
        d = Matrix(1, 1, [[1]])
        res = solve_leontief(A, d)
        assert res["status"] == "SUCCESS"
        assert res["x"] == [Fraction(1001)]


# =========================================================================
# GRUPO 3 — Verificación
# =========================================================================

class TestVerification:

    def test_verification_coincides_on_success(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        res = solve_leontief(A, d)
        assert res["verification"] is not None
        assert res["verification"]["coincide"] is True
        assert "Correcto" in res["verification"]["detail_latex"]

    def test_verification_has_product_matrix(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        res = solve_leontief(A, d)
        assert res["verification"]["product"] is not None

    def test_verification_absent_on_no_solution(self):
        A = Matrix(2, 2, [[1, 0], [0, 1]])
        d = Matrix(2, 1, [[5], [3]])
        res = solve_leontief(A, d)
        assert res["status"] == "NO_SOLUTION"
        assert res["verification"] is None


# =========================================================================
# GRUPO 4 — Estados especiales
# =========================================================================

class TestSpecialStates:

    def test_singular_I_minus_A_inconsistent(self):
        """A = [[0, 1], [1, 0]] → I - A = [[1, -1], [-1, 1]].
        Con d = [1, 0] el sistema es inconsistente."""
        A = Matrix(2, 2, [[0, 1], [1, 0]])
        d = Matrix(2, 1, [[1], [0]])
        res = solve_leontief(A, d)
        assert res["status"] == "NO_SOLUTION"
        assert res["x"] is None

    def test_singular_I_minus_A_consistent(self):
        """A = [[0, 1], [1, 0]] con d = [0, 0]: infinitas soluciones."""
        A = Matrix(2, 2, [[0, 1], [1, 0]])
        d = Matrix(2, 1, [[0], [0]])
        res = solve_leontief(A, d)
        assert res["status"] == "INFINITE_SOLUTIONS"

    def test_identity_A_no_demand(self):
        """A = I, d = 0 → (I - A) = 0 → infinitas soluciones."""
        A = Matrix(2, 2, [[1, 0], [0, 1]])
        d = Matrix(2, 1, [[0], [0]])
        res = solve_leontief(A, d)
        assert res["status"] == "INFINITE_SOLUTIONS"

    def test_identity_A_with_demand_inconsistent(self):
        """A = I, d = [5, 3] → (I - A) = 0 → inconsistente."""
        A = Matrix(2, 2, [[1, 0], [0, 1]])
        d = Matrix(2, 1, [[5], [3]])
        res = solve_leontief(A, d)
        assert res["status"] == "NO_SOLUTION"

    def test_1x1_identity_inconsistent(self):
        A = Matrix(1, 1, [[1]])
        d = Matrix(1, 1, [[5]])
        res = solve_leontief(A, d)
        assert res["status"] == "NO_SOLUTION"

    def test_1x1_identity_zero_demand(self):
        A = Matrix(1, 1, [[1]])
        d = Matrix(1, 1, [[0]])
        res = solve_leontief(A, d)
        assert res["status"] == "INFINITE_SOLUTIONS"


# =========================================================================
# GRUPO 5 — Validación de inputs
# =========================================================================

class TestValidation:

    def test_A_not_matrix(self):
        res = solve_leontief([[1, 0], [0, 1]], Matrix(2, 1, [[1], [2]]))
        assert res["status"] == "ERROR"
        assert "Matrix" in res["message"]

    def test_d_not_matrix(self):
        res = solve_leontief(Matrix(2, 2, [[0, 0], [0, 0]]), [[1], [2]])
        assert res["status"] == "ERROR"

    def test_A_not_square(self):
        res = solve_leontief(
            Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]),
            Matrix(2, 1, [[1], [2]]),
        )
        assert res["status"] == "ERROR"
        assert "cuadrada" in res["message"]

    def test_d_not_column(self):
        res = solve_leontief(
            Matrix(2, 2, [[0, 0], [0, 0]]),
            Matrix(1, 2, [[1, 2]]),
        )
        assert res["status"] == "ERROR"
        assert "columna" in res["message"]

    def test_d_wrong_length(self):
        res = solve_leontief(
            Matrix(2, 2, [[0, 0], [0, 0]]),
            Matrix(3, 1, [[1], [2], [3]]),
        )
        assert res["status"] == "ERROR"

    def test_sector_names_not_list(self):
        res = solve_leontief(
            Matrix(2, 2, [[0, 0], [0, 0]]),
            Matrix(2, 1, [[1], [2]]),
            sector_names="Agro",
        )
        assert res["status"] == "ERROR"
        assert "lista" in res["message"]

    def test_sector_names_wrong_length(self):
        res = solve_leontief(
            Matrix(2, 2, [[0, 0], [0, 0]]),
            Matrix(2, 1, [[1], [2]]),
            sector_names=["Agro", "Industria", "Servicios"],
        )
        assert res["status"] == "ERROR"
        assert "3" in res["message"] and "2" in res["message"]

    def test_sector_names_non_string_element(self):
        res = solve_leontief(
            Matrix(2, 2, [[0, 0], [0, 0]]),
            Matrix(2, 1, [[1], [2]]),
            sector_names=["Agro", 42],
        )
        assert res["status"] == "ERROR"
        assert "strings" in res["message"]


# =========================================================================
# GRUPO 6 — Contrato y no mutación
# =========================================================================

_EXPECTED_KEYS = {
    "status", "message", "A", "d", "sector_names",
    "I_minus_A", "I_minus_A_latex", "d_latex",
    "x", "x_latex", "solution", "solution_param",
    "steps", "verification", "interpretation", "error_cell",
}


class TestContract:

    def test_success_keys(self):
        A = Matrix(1, 1, [[0]])
        d = Matrix(1, 1, [[5]])
        res = solve_leontief(A, d)
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_no_solution_keys(self):
        A = Matrix(1, 1, [[1]])
        d = Matrix(1, 1, [[5]])
        res = solve_leontief(A, d)
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_infinite_keys(self):
        A = Matrix(1, 1, [[1]])
        d = Matrix(1, 1, [[0]])
        res = solve_leontief(A, d)
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_error_keys(self):
        res = solve_leontief([[1]], Matrix(1, 1, [[1]]))
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_does_not_mutate_A(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        snapshot = A.clone()
        d = Matrix(2, 1, [[2], [3]])
        solve_leontief(A, d)
        assert A == snapshot

    def test_does_not_mutate_d(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        snapshot = d.clone()
        solve_leontief(A, d)
        assert d == snapshot

    def test_interpretation_present_on_all_states(self):
        # SUCCESS
        res_ok = solve_leontief(Matrix(1, 1, [[0]]), Matrix(1, 1, [[5]]))
        assert len(res_ok["interpretation"]) > 30
        # NO_SOLUTION
        res_no = solve_leontief(Matrix(1, 1, [[1]]), Matrix(1, 1, [[5]]))
        assert len(res_no["interpretation"]) > 30
        # INFINITE
        res_inf = solve_leontief(Matrix(1, 1, [[1]]), Matrix(1, 1, [[0]]))
        assert len(res_inf["interpretation"]) > 30

    def test_steps_present_on_all_states(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        res = solve_leontief(A, d)
        assert len(res["steps"]) >= 1
        assert "I" in res["steps"][0]["description"]
        assert "A" in res["steps"][0]["description"]

    def test_first_step_has_partitioned_latex(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        res = solve_leontief(A, d)
        assert res["steps"][0]["detail_latex"] is not None
        # La partición usa array con línea vertical
        assert "array" in res["steps"][0]["detail_latex"]
        assert "|" in res["steps"][0]["detail_latex"]

    def test_latex_present_on_success(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        res = solve_leontief(A, d)
        assert res["I_minus_A_latex"] is not None
        assert "bmatrix" in res["I_minus_A_latex"]
        assert res["d_latex"] is not None
        assert "bmatrix" in res["d_latex"]
        assert res["x_latex"] is not None
        assert "bmatrix" in res["x_latex"]

    def test_I_minus_A_returned_on_success(self):
        A = Matrix(2, 2, [[Fraction(1, 2), 0], [0, Fraction(1, 4)]])
        d = Matrix(2, 1, [[2], [3]])
        res = solve_leontief(A, d)
        assert res["I_minus_A"] is not None
        assert res["I_minus_A"].get(0, 0) == Fraction(1, 2)
        assert res["I_minus_A"].get(0, 1) == Fraction(0)
        assert res["I_minus_A"].get(1, 0) == Fraction(0)
        assert res["I_minus_A"].get(1, 1) == Fraction(3, 4)


# =========================================================================
# GRUPO 7 — sector_names
# =========================================================================

class TestSectorNames:

    def test_default_names(self):
        A = Matrix(2, 2, [[0, 0], [0, 0]])
        d = Matrix(2, 1, [[1], [2]])
        res = solve_leontief(A, d)
        assert res["sector_names"] == ["x_1", "x_2"]
        assert "x_1 = 1" in res["interpretation"]
        assert "x_2 = 2" in res["interpretation"]

    def test_custom_names(self):
        A = Matrix(2, 2, [[0, 0], [0, 0]])
        d = Matrix(2, 1, [[1], [2]])
        res = solve_leontief(A, d, sector_names=["Agro", "Industria"])
        assert res["sector_names"] == ["Agro", "Industria"]
        assert "Agro = 1" in res["interpretation"]
        assert "Industria = 2" in res["interpretation"]

    def test_custom_names_on_infinite_still_present(self):
        A = Matrix(2, 2, [[1, 0], [0, 1]])
        d = Matrix(2, 1, [[0], [0]])
        res = solve_leontief(A, d, sector_names=["Agro", "Industria"])
        assert res["sector_names"] == ["Agro", "Industria"]

    def test_default_names_do_not_mutate_external_list(self):
        """Si se pasa sector_names, no se debe mutar la lista del caller."""
        A = Matrix(2, 2, [[0, 0], [0, 0]])
        d = Matrix(2, 1, [[1], [2]])
        original = ["Agro", "Industria"]
        solve_leontief(A, d, sector_names=original)
        assert original == ["Agro", "Industria"]