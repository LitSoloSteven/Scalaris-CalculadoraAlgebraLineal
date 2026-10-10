"""Tests para test_independence.

Dado un conjunto {v_1, ..., v_k} de vectores columna en R^n, se decide
si son linealmente independientes. Reutiliza solve_homogeneous sobre
A = [v_1 | ... | v_k] y mapea el resultado:

  - TRIVIAL_ONLY  → INDEPENDENT
  - NON_TRIVIAL   → DEPENDENT, con una relación de dependencia explícita.

Estados:
  - INDEPENDENT: los vectores son LI. rank = k.
  - DEPENDENT: los vectores son LD. rank < k.
  - ERROR: input inválido (lista vacía, no Matrix, dimensiones
    inconsistentes, shape no columna).
"""
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.independence import test_independence


# =========================================================================
# GRUPO 1 — Casos INDEPENDENT
# =========================================================================

class TestIndependent:

    def test_single_nonzero_vector(self):
        v = Matrix(2, 1, [[3], [4]])
        res = test_independence([v])
        assert res["status"] == "INDEPENDENT"
        assert res["is_independent"] is True
        assert res["rank"] == 1
        assert res["num_vectors"] == 1
        assert res["dim"] == 2
        assert res["free_cols"] == []
        assert res["dependency_relations"] == []

    def test_canonical_basis_r2(self):
        e1 = Matrix(2, 1, [[1], [0]])
        e2 = Matrix(2, 1, [[0], [1]])
        res = test_independence([e1, e2])
        assert res["status"] == "INDEPENDENT"
        assert res["rank"] == 2

    def test_canonical_basis_r3(self):
        e1 = Matrix(3, 1, [[1], [0], [0]])
        e2 = Matrix(3, 1, [[0], [1], [0]])
        e3 = Matrix(3, 1, [[0], [0], [1]])
        res = test_independence([e1, e2, e3])
        assert res["status"] == "INDEPENDENT"
        assert res["rank"] == 3

    def test_two_independent_vectors(self):
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[3], [4]])
        res = test_independence([v1, v2])
        assert res["status"] == "INDEPENDENT"
        assert res["rank"] == 2

    def test_three_independent_in_r3(self):
        v1 = Matrix(3, 1, [[1], [0], [1]])
        v2 = Matrix(3, 1, [[0], [1], [1]])
        v3 = Matrix(3, 1, [[1], [1], [0]])
        res = test_independence([v1, v2, v3])
        assert res["status"] == "INDEPENDENT"

    def test_fewer_vectors_than_dim(self):
        """2 vectores LI en R³: subespacio de dimensión 2."""
        v1 = Matrix(3, 1, [[1], [0], [0]])
        v2 = Matrix(3, 1, [[0], [1], [0]])
        res = test_independence([v1, v2])
        assert res["status"] == "INDEPENDENT"
        assert res["rank"] == 2
        assert res["dim"] == 3

    def test_fractional_entries(self):
        v1 = Matrix(2, 1, [[Fraction(1, 2)], [Fraction(1, 3)]])
        v2 = Matrix(2, 1, [[Fraction(1, 4)], [Fraction(1, 5)]])
        res = test_independence([v1, v2])
        assert res["status"] == "INDEPENDENT"


# =========================================================================
# GRUPO 2 — Casos DEPENDENT
# =========================================================================

class TestDependent:

    def test_single_zero_vector(self):
        v = Matrix(2, 1, [[0], [0]])
        res = test_independence([v])
        assert res["status"] == "DEPENDENT"
        assert res["is_independent"] is False
        assert res["rank"] == 0
        assert res["free_cols"] == [0]

    def test_two_dependent_vectors_r2(self):
        """v2 = 2·v1."""
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[2], [4]])
        res = test_independence([v1, v2])
        assert res["status"] == "DEPENDENT"
        assert res["rank"] == 1
        assert res["free_cols"] == [1]

    def test_three_dependent_in_r3(self):
        """v3 = v1 + v2."""
        v1 = Matrix(3, 1, [[1], [0], [0]])
        v2 = Matrix(3, 1, [[0], [1], [0]])
        v3 = Matrix(3, 1, [[1], [1], [0]])
        res = test_independence([v1, v2, v3])
        assert res["status"] == "DEPENDENT"
        assert res["rank"] == 2

    def test_four_vectors_in_r3_always_dependent(self):
        """4 vectores en R³ son siempre LD."""
        v1 = Matrix(3, 1, [[1], [0], [0]])
        v2 = Matrix(3, 1, [[0], [1], [0]])
        v3 = Matrix(3, 1, [[0], [0], [1]])
        v4 = Matrix(3, 1, [[1], [1], [1]])
        res = test_independence([v1, v2, v3, v4])
        assert res["status"] == "DEPENDENT"
        assert res["rank"] == 3

    def test_all_zeros_multiple(self):
        v1 = Matrix(2, 1, [[0], [0]])
        v2 = Matrix(2, 1, [[0], [0]])
        res = test_independence([v1, v2])
        assert res["status"] == "DEPENDENT"
        assert res["rank"] == 0

    def test_dependency_relation_present(self):
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[2], [4]])
        res = test_independence([v1, v2])
        assert len(res["dependency_relations"]) >= 1
        rel = res["dependency_relations"][0]
        assert "relation_latex" in rel
        assert "relation_plain" in rel
        # La relación debe contener los coeficientes del kernel
        # (cualquier múltiplo es válido; solo verificamos que menciona v_1, v_2)
        assert "v_1" in rel["relation_plain"] or "v_2" in rel["relation_plain"]

    def test_dependency_relation_equals_zero_on_substitution(self):
        """La relación c hallada satisface Σ c_i · v_i = 0."""
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[2], [4]])
        res = test_independence([v1, v2])
        rel = res["dependency_relations"][0]
        coeffs = rel["coefficients"]
        # Σ coeffs[i] · v_i = 0
        total_row0 = Fraction(0)
        total_row1 = Fraction(0)
        for c, v in zip(coeffs, [v1, v2]):
            total_row0 += c * Fraction(v.get(0, 0))
            total_row1 += c * Fraction(v.get(1, 0))
        assert total_row0 == 0
        assert total_row1 == 0

    def test_multiple_dependency_relations(self):
        """3 vectores en R² con rank 1 → 2 direcciones libres."""
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[2], [4]])
        v3 = Matrix(2, 1, [[3], [6]])
        res = test_independence([v1, v2, v3])
        assert res["status"] == "DEPENDENT"
        assert res["rank"] == 1
        assert len(res["dependency_relations"]) == 2  # free_cols = [1, 2]

    def test_fractional_dependent(self):
        v1 = Matrix(2, 1, [[Fraction(1, 2)], [Fraction(1)]])
        v2 = Matrix(2, 1, [[Fraction(1)], [Fraction(2)]])
        res = test_independence([v1, v2])
        assert res["status"] == "DEPENDENT"


# =========================================================================
# GRUPO 3 — Precisión
# =========================================================================

class TestPrecision:

    def test_large_denominator_does_not_truncate(self):
        """A = [[1001, 0], [1, 0]] con vectores columna."""
        v1 = Matrix(2, 1, [["1001"], ["1"]])
        v2 = Matrix(2, 1, [["0"], ["0"]])
        res = test_independence([v1, v2])
        # v2 es cero → dependientes
        assert res["status"] == "DEPENDENT"

    def test_large_denominator_independent(self):
        v1 = Matrix(2, 1, [[Fraction(1, 1001)], [Fraction(0)]])
        v2 = Matrix(2, 1, [[Fraction(0)], [Fraction(1, 1001)]])
        res = test_independence([v1, v2])
        assert res["status"] == "INDEPENDENT"


# =========================================================================
# GRUPO 4 — Validación
# =========================================================================

class TestValidation:

    def test_empty_list_rejected(self):
        res = test_independence([])
        assert res["status"] == "ERROR"

    def test_non_list_rejected(self):
        res = test_independence("no soy lista")
        assert res["status"] == "ERROR"

    def test_non_matrix_in_list(self):
        v = Matrix(2, 1, [[1], [0]])
        res = test_independence([v, "no soy Matrix"])
        assert res["status"] == "ERROR"

    def test_row_vector_rejected(self):
        """Los vectores deben ser columna n×1, no fila 1×n."""
        v1 = Matrix(2, 1, [[1], [0]])
        v2 = Matrix(1, 2, [[0, 1]])
        res = test_independence([v1, v2])
        assert res["status"] == "ERROR"

    def test_inconsistent_dimensions_rejected(self):
        v1 = Matrix(2, 1, [[1], [0]])
        v2 = Matrix(3, 1, [[0], [1], [0]])
        res = test_independence([v1, v2])
        assert res["status"] == "ERROR"

    def test_non_column_matrix_rejected(self):
        """Matriz 2×2 como vector no es válida."""
        v = Matrix(2, 2, [[1, 2], [3, 4]])
        res = test_independence([v])
        assert res["status"] == "ERROR"


# =========================================================================
# GRUPO 5 — Contrato
# =========================================================================

_EXPECTED_KEYS = {
    "status", "message", "is_independent",
    "rank", "num_vectors", "dim",
    "pivot_cols", "free_cols",
    "dependency_relations",
    "reduced_matrix", "steps",
    "explanation", "error_cell",
}


class TestContract:

    def test_independent_keys(self):
        v = Matrix(2, 1, [[1], [0]])
        res = test_independence([v])
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_dependent_keys(self):
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[2], [4]])
        res = test_independence([v1, v2])
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_error_keys(self):
        res = test_independence([])
        assert set(res.keys()) == _EXPECTED_KEYS

    def test_does_not_mutate_inputs(self):
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[3], [4]])
        s1, s2 = v1.clone(), v2.clone()
        test_independence([v1, v2])
        assert v1 == s1
        assert v2 == s2

    def test_explanation_independent(self):
        v1 = Matrix(2, 1, [[1], [0]])
        v2 = Matrix(2, 1, [[0], [1]])
        res = test_independence([v1, v2])
        assert "independiente" in res["explanation"].lower()

    def test_explanation_dependent(self):
        v1 = Matrix(2, 1, [[1], [2]])
        v2 = Matrix(2, 1, [[2], [4]])
        res = test_independence([v1, v2])
        assert "dependiente" in res["explanation"].lower()

    def test_explanation_mentions_rank(self):
        v1 = Matrix(2, 1, [[1], [0]])
        v2 = Matrix(2, 1, [[0], [1]])
        res = test_independence([v1, v2])
        assert "2" in res["explanation"]  # rank

    def test_reduced_matrix_present_on_success(self):
        v1 = Matrix(2, 1, [[1], [0]])
        v2 = Matrix(2, 1, [[0], [1]])
        res = test_independence([v1, v2])
        assert res["reduced_matrix"] is not None

    def test_message_present(self):
        v = Matrix(2, 1, [[1], [0]])
        res = test_independence([v])
        assert len(res["message"]) > 10