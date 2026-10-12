"""Tests para los dos métodos de cálculo de determinantes de P6.

  - determinant_by_cofactors: expansión recursiva con traza de signos y menores.
  - determinant_by_lu: factorización con pivoteo parcial + producto de la
    diagonal × (-1)^swaps.

Ambos deben devolver el MISMO resultado exacto en los casos de referencia,
y coincidir con MatrixOpsSolver.determinant (que usa eliminación a
triangular superior sin traza pedagógica).
"""
from fractions import Fraction

import pytest

from src.backend.constants import COFACTOR_MAX_DIMENSION
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.determinants import (
    determinant_by_cofactors,
    determinant_by_lu,
    recommend_method,
)
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver


# =========================================================================
# GRUPO 1 — Cofactores: casos base
# =========================================================================

class TestCofactorBasic:

    def test_cofactor_1x1(self):
        A = Matrix(1, 1, [[5]])
        res = determinant_by_cofactors(A)
        assert res["status"] == "SUCCESS"
        assert res["determinant"] == Fraction(5)
        assert res["method"] == "cofactores"

    def test_cofactor_2x2(self):
        A = Matrix(2, 2, [[4, 6], [3, 8]])
        res = determinant_by_cofactors(A)
        assert res["determinant"] == Fraction(14)

    def test_cofactor_2x2_negative(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(-2)

    def test_cofactor_3x3(self):
        A = Matrix(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(1)

    def test_cofactor_3x3_ppt_page_20(self):
        A = Matrix(3, 3, [[1, -4, 2], [-2, 8, -9], [-1, 7, 0]])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(15)

    def test_cofactor_4x4(self):
        A = Matrix(4, 4, [
            [0, 1, 1, 0],
            [1, 0, 1, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 1],
        ])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(2)

    def test_cofactor_identity(self):
        A = Matrix(3, 3, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(1)


# =========================================================================
# GRUPO 2 — Cofactores: singulares y fracciones
# =========================================================================

class TestCofactorSingularAndFractions:

    def test_cofactor_singular_dependent_rows(self):
        A = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(0)

    def test_cofactor_singular_duplicate_rows(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [1, 2, 3]])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(0)

    def test_cofactor_singular_zero_matrix(self):
        A = Matrix(2, 2, [[0, 0], [0, 0]])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(0)

    def test_cofactor_fractional_entries(self):
        A = Matrix(2, 2, [
            [Fraction(1, 2), Fraction(1, 3)],
            [Fraction(1, 4), Fraction(1, 5)],
        ])
        # (1/2)(1/5) - (1/3)(1/4) = 1/10 - 1/12 = 1/60
        assert determinant_by_cofactors(A)["determinant"] == Fraction(1, 60)

    def test_cofactor_preserves_large_denominator(self):
        A = Matrix(2, 2, [
            [Fraction(1, 1001), 0],
            [0, Fraction(1, 1001)],
        ])
        assert determinant_by_cofactors(A)["determinant"] == Fraction(1, 1001 * 1001)


# =========================================================================
# GRUPO 3 — Cofactores: traza de signos y menores
# =========================================================================

class TestCofactorSteps:

    def test_cofactor_has_steps(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        res = determinant_by_cofactors(A)
        assert len(res["steps"]) >= 2

    def test_cofactor_step_1_mentions_sign_pattern(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        res = determinant_by_cofactors(A)
        first = res["steps"][0]
        assert "signo" in first["description"].lower() or "expansión" in first["description"].lower()
        assert first["detail_latex"] is not None

    def test_cofactor_minors_list_has_n_elements(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        res = determinant_by_cofactors(A)
        assert len(res["minors"]) == 3
        for m in res["minors"]:
            assert "row" in m and "col" in m
            assert "value" in m and isinstance(m["value"], Fraction)
            assert "sign" in m and m["sign"] in (1, -1)

    def test_cofactor_minor_values_correct_3x3(self):
        """A = [[1,2,3],[4,5,6],[7,8,10]].
        M[0][0] = det([[5,6],[8,10]]) = 50 - 48 = 2
        M[0][1] = det([[4,6],[7,10]]) = 40 - 42 = -2
        M[0][2] = det([[4,5],[7,8]]) = 32 - 35 = -3
        det = 1·2 - 2·(-2) + 3·(-3) = 2 + 4 - 9 = -3
        """
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        res = determinant_by_cofactors(A)
        minors = {(m["row"], m["col"]): m["value"] for m in res["minors"]}
        assert minors[(0, 0)] == Fraction(2)
        assert minors[(0, 1)] == Fraction(-2)
        assert minors[(0, 2)] == Fraction(-3)
        assert res["determinant"] == Fraction(-3)

    def test_cofactor_step_latex_present(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        res = determinant_by_cofactors(A)
        for step in res["steps"]:
            assert step["detail_latex"] is not None


# =========================================================================
# GRUPO 4 — Cofactores: validación
# =========================================================================

class TestCofactorValidation:

    def test_cofactor_non_square_rejected(self):
        A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
        res = determinant_by_cofactors(A)
        assert res["status"] == "ERROR"
        assert "cuadrada" in res["message"].lower()

    def test_cofactor_above_limit_rejected(self):
        n = COFACTOR_MAX_DIMENSION + 1
        A = Matrix(n, n, [[1 if i == j else 0 for j in range(n)] for i in range(n)])
        res = determinant_by_cofactors(A)
        assert res["status"] == "ERROR"
        assert "cofactor" in res["message"].lower() or "límite" in res["message"].lower()

    def test_cofactor_at_limit_accepted(self):
        n = COFACTOR_MAX_DIMENSION
        A = Matrix(n, n, [[1 if i == j else 0 for j in range(n)] for i in range(n)])
        res = determinant_by_cofactors(A)
        assert res["status"] == "SUCCESS"
        assert res["determinant"] == Fraction(1)

    def test_cofactor_non_matrix_rejected(self):
        res = determinant_by_cofactors([[1, 2], [3, 4]])
        assert res["status"] == "ERROR"


# =========================================================================
# GRUPO 5 — LU: casos base
# =========================================================================

class TestLUBasic:

    def test_lu_1x1(self):
        A = Matrix(1, 1, [[5]])
        res = determinant_by_lu(A)
        assert res["status"] == "SUCCESS"
        assert res["determinant"] == Fraction(5)
        assert res["method"] == "lu"

    def test_lu_2x2(self):
        A = Matrix(2, 2, [[4, 6], [3, 8]])
        assert determinant_by_lu(A)["determinant"] == Fraction(14)

    def test_lu_2x2_negative(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        assert determinant_by_lu(A)["determinant"] == Fraction(-2)

    def test_lu_3x3(self):
        A = Matrix(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
        assert determinant_by_lu(A)["determinant"] == Fraction(1)

    def test_lu_3x3_ppt_page_20(self):
        A = Matrix(3, 3, [[1, -4, 2], [-2, 8, -9], [-1, 7, 0]])
        assert determinant_by_lu(A)["determinant"] == Fraction(15)

    def test_lu_4x4_with_pivoting(self):
        A = Matrix(4, 4, [
            [0, 1, 1, 0],
            [1, 0, 1, 0],
            [1, 1, 0, 0],
            [0, 0, 0, 1],
        ])
        assert determinant_by_lu(A)["determinant"] == Fraction(2)

    def test_lu_identity(self):
        A = Matrix(3, 3, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        assert determinant_by_lu(A)["determinant"] == Fraction(1)

    def test_lu_10x10_identity(self):
        n = 10
        A = Matrix(n, n, [[1 if i == j else 0 for j in range(n)] for i in range(n)])
        assert determinant_by_lu(A)["determinant"] == Fraction(1)


# =========================================================================
# GRUPO 6 — LU: pivoteo y signo
# =========================================================================

class TestLUWithPivoting:

    def test_lu_swap_detected_and_sign_flipped(self):
        """A = [[0, 1], [1, 0]]. det = -1. Necesita 1 swap."""
        A = Matrix(2, 2, [[0, 1], [1, 0]])
        res = determinant_by_lu(A)
        assert res["status"] == "SUCCESS"
        assert res["determinant"] == Fraction(-1)
        assert res["swap_count"] == 1

    def test_lu_no_swap_sign_positive(self):
        A = Matrix(2, 2, [[2, 1], [1, 2]])
        res = determinant_by_lu(A)
        assert res["swap_count"] == 0
        assert res["determinant"] == Fraction(3)

    def test_lu_3x3_with_two_swaps(self):
        """Permutación que requiere 2 swaps. det = (-1)^2 = 1."""
        A = Matrix(3, 3, [
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ])
        res = determinant_by_lu(A)
        assert res["status"] == "SUCCESS"
        assert res["determinant"] == Fraction(1)
        assert res["swap_count"] >= 1  # al menos 1 swap

    def test_lu_swap_count_matches_sign(self):
        """El signo del determinante es (-1)^swap_count × ∏ pivotes."""
        A = Matrix(4, 4, [
            [0, 2, 1, 3],
            [4, 1, 2, 1],
            [1, 3, 0, 2],
            [2, 0, 1, 1],
        ])
        res = determinant_by_lu(A)
        expected_sign = 1 if res["swap_count"] % 2 == 0 else -1
        # El producto de los pivotes debe tener el signo opuesto al det si
        # swap_count es impar
        pivots_product = Fraction(1)
        for p in res["pivots"]:
            pivots_product *= p
        assert res["determinant"] == expected_sign * pivots_product

    def test_lu_pivots_list_present(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        res = determinant_by_lu(A)
        assert len(res["pivots"]) == 3
        assert all(isinstance(p, Fraction) for p in res["pivots"])


# =========================================================================
# GRUPO 7 — LU: singulares y fracciones
# =========================================================================

class TestLUSingularAndFractions:

    def test_lu_singular_dependent_rows(self):
        A = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
        assert determinant_by_lu(A)["determinant"] == Fraction(0)

    def test_lu_singular_duplicate_rows(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [1, 2, 3]])
        assert determinant_by_lu(A)["determinant"] == Fraction(0)

    def test_lu_singular_zero_matrix(self):
        A = Matrix(2, 2, [[0, 0], [0, 0]])
        assert determinant_by_lu(A)["determinant"] == Fraction(0)

    def test_lu_fractional_entries(self):
        A = Matrix(2, 2, [
            [Fraction(1, 2), Fraction(1, 3)],
            [Fraction(1, 4), Fraction(1, 5)],
        ])
        assert determinant_by_lu(A)["determinant"] == Fraction(1, 60)

    def test_lu_preserves_large_denominator(self):
        A = Matrix(2, 2, [
            [Fraction(1, 1001), 0],
            [0, Fraction(1, 1001)],
        ])
        assert determinant_by_lu(A)["determinant"] == Fraction(1, 1001 * 1001)


# =========================================================================
# GRUPO 8 — LU: validación
# =========================================================================

class TestLUValidation:

    def test_lu_non_square_rejected(self):
        A = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
        res = determinant_by_lu(A)
        assert res["status"] == "ERROR"
        assert "cuadrada" in res["message"].lower()

    def test_lu_non_matrix_rejected(self):
        res = determinant_by_lu([[1, 2], [3, 4]])
        assert res["status"] == "ERROR"


# =========================================================================
# GRUPO 9 — Cross-check entre los tres métodos
# =========================================================================

class TestCrossCheck:

    @pytest.mark.parametrize("data", [
        [[4, 6], [3, 8]],
        [[1, 2], [3, 4]],
        [[1, 2, 3], [0, 1, 4], [5, 6, 0]],
        [[1, -4, 2], [-2, 8, -9], [-1, 7, 0]],
        [[1, 2, 3], [4, 5, 6], [7, 8, 10]],
        [[2, 0, 0], [0, 3, 0], [0, 0, 5]],
        [[0, 1], [1, 0]],
        [[1, 2], [2, 4]],
        [[5]],
        [[0]],
    ])
    def test_cofactors_lu_and_ops_agree(self, data):
        n = len(data)
        A = Matrix(n, n, data)
        ops = MatrixOpsSolver()
        det_ops = ops.determinant(A)
        det_cof = determinant_by_cofactors(A)["determinant"]
        det_lu = determinant_by_lu(A)["determinant"]
        assert det_cof == det_ops, f"Cofactores no coincide: {det_cof} vs {det_ops}"
        assert det_lu == det_ops, f"LU no coincide: {det_lu} vs {det_ops}"

    def test_cofactors_lu_agree_with_fractions(self):
        A = Matrix(3, 3, [
            [Fraction(1, 2), Fraction(1, 3), Fraction(1, 4)],
            [Fraction(1, 5), Fraction(1, 6), Fraction(1, 7)],
            [Fraction(1, 8), Fraction(1, 9), Fraction(1, 10)],
        ])
        det_cof = determinant_by_cofactors(A)["determinant"]
        det_lu = determinant_by_lu(A)["determinant"]
        assert det_cof == det_lu

    def test_transpose_property_holds_both_methods(self):
        """det(A) = det(Aᵀ) en ambos métodos."""
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        ops = MatrixOpsSolver()
        AT = ops.transpose(A)
        assert determinant_by_cofactors(A)["determinant"] == determinant_by_cofactors(AT)["determinant"]
        assert determinant_by_lu(A)["determinant"] == determinant_by_lu(AT)["determinant"]


# =========================================================================
# GRUPO 10 — Recomendación de eficiencia
# =========================================================================

class TestRecommendation:

    def test_recommendation_returns_dict_with_contract_keys(self):
        res = recommend_method(3)
        assert "recommended" in res
        assert "cofactor_complexity" in res
        assert "lu_complexity" in res
        assert "reason" in res
        assert "cofactor_available" in res

    def test_recommendation_small_n_prefers_cofactors(self):
        for n in (1, 2, 3, 4):
            res = recommend_method(n)
            assert res["recommended"] == "cofactores", f"n={n}"

    def test_recommendation_large_n_prefers_lu(self):
        for n in (5, 6, 10, 20):
            res = recommend_method(n)
            assert res["recommended"] == "lu", f"n={n}"

    def test_recommendation_cofactor_availability(self):
        assert recommend_method(8)["cofactor_available"] is True
        assert recommend_method(9)["cofactor_available"] is False
        assert recommend_method(20)["cofactor_available"] is False

    def test_recommendation_complexities_are_labelled(self):
        res = recommend_method(5)
        assert "O(n!)" in res["cofactor_complexity"] or "factorial" in res["cofactor_complexity"].lower()
        assert "O(n" in res["lu_complexity"]

    def test_recommendation_invalid_n(self):
        assert recommend_method(0)["recommended"] == "lu" or "error" in recommend_method(0)


# =========================================================================
# GRUPO 11 — Contrato y no mutación
# =========================================================================

_EXPECTED_KEYS = {
    "status", "message", "method", "determinant", "determinant_str",
    "steps", "minors", "swap_count", "pivots", "error_cell",
}


class TestContract:

    def test_cofactor_contract_keys(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = determinant_by_cofactors(A)
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_lu_contract_keys(self):
        A = Matrix(2, 2, [[1, 2], [3, 4]])
        res = determinant_by_lu(A)
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_cofactor_does_not_mutate(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        snap = A.clone()
        determinant_by_cofactors(A)
        assert A == snap

    def test_lu_does_not_mutate(self):
        A = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        snap = A.clone()
        determinant_by_lu(A)
        assert A == snap

    def test_cofactor_determinant_str_present(self):
        A = Matrix(2, 2, [[1, 3], [3, 4]])
        res = determinant_by_cofactors(A)
        assert res["determinant_str"] == "-5"

    def test_lu_determinant_str_present(self):
        A = Matrix(2, 2, [[1, 3], [3, 4]])
        res = determinant_by_lu(A)
        assert res["determinant_str"] == "-5"