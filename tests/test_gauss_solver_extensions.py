"""Tests para las extensiones opt-in de GaussSolver.

Dos flags nuevos, ambos desactivados por defecto:
  - capture_multipliers: persiste los multiplicadores de la eliminación
    como lista de dicts {row, col, value}. Solo válido con
    pivot_strategy='none' (con pivoteo parcial los multiplicadores
    requieren seguimiento de permutaciones, que es otra feature: PA = LU).
  - pivot_strategy: 'partial' (default, comportamiento actual) o 'none'
    (prohibido intercambiar filas; si aparece un pivote cero, se registra
    en self.zero_pivots y se continúa).

Contrato duro: con defaults (pivot_strategy='partial',
capture_multipliers=False), el solver se comporta byte a byte igual que
antes de esta extensión. check_dry_refactor debe dar 135 pasos idénticos.
"""
from fractions import Fraction

import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver


# =========================================================================
# GRUPO 1 — Defaults no cambian el comportamiento
# =========================================================================

class TestDefaultsPreserved:

    def test_pivot_strategy_default_is_partial(self):
        gs = GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]))
        assert gs.pivot_strategy == "partial"

    def test_capture_multipliers_default_is_false(self):
        gs = GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]))
        assert gs.capture_multipliers is False

    def test_multipliers_default_is_empty(self):
        gs = GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]))
        assert gs.multipliers == []

    def test_zero_pivots_default_is_empty(self):
        gs = GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]))
        assert gs.zero_pivots == []

    def test_default_steps_identical_to_explicit_partial(self):
        """Los steps con defaults son byte a byte los mismos que con
        pivot_strategy='partial', capture_multipliers=False explícitos."""
        data = [
            ["2", "1", "-1", "8"],
            ["-3", "-1", "2", "-11"],
            ["-2", "1", "2", "-3"],
        ]
        gs_default = GaussSolver(Matrix(3, 4, data))
        gs_explicit = GaussSolver(
            Matrix(3, 4, data),
            pivot_strategy="partial",
            capture_multipliers=False,
        )
        gs_default.solve()
        gs_explicit.solve()
        assert len(gs_default.steps) == len(gs_explicit.steps)
        for sd, se in zip(gs_default.steps, gs_explicit.steps):
            assert sd["description"] == se["description"]
            assert sd["matrix"] == se["matrix"]

    def test_multipliers_stay_empty_after_default_solve(self):
        gs = GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]))
        gs.solve()
        assert gs.multipliers == []

    def test_zero_pivots_stay_empty_with_partial(self):
        """Con pivoteo parcial (default), zero_pivots nunca se usa."""
        gs = GaussSolver(Matrix(2, 3, [["0", "1", "0"], ["1", "0", "0"]]),
                         pivot_strategy="partial")
        gs.solve_reduction()
        assert gs.zero_pivots == []


# =========================================================================
# GRUPO 2 — Validación de kwargs
# =========================================================================

class TestKwargsValidation:

    def test_invalid_pivot_strategy_raises(self):
        with pytest.raises(ValueError, match="pivot_strategy"):
            GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]),
                        pivot_strategy="foo")

    def test_capture_multipliers_with_partial_raises(self):
        with pytest.raises(ValueError, match="capture_multipliers"):
            GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]),
                        capture_multipliers=True,
                        pivot_strategy="partial")

    def test_capture_multipliers_with_default_pivot_raises(self):
        """capture_multipliers=True sin especificar pivot_strategy usa el
        default 'partial', que es incompatible."""
        with pytest.raises(ValueError, match="capture_multipliers"):
            GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]),
                        capture_multipliers=True)

    def test_capture_multipliers_with_none_is_valid(self):
        # No debe lanzar
        GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]),
                    capture_multipliers=True,
                    pivot_strategy="none")

    def test_pivot_strategy_none_without_capture_is_valid(self):
        # No debe lanzar
        GaussSolver(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]),
                    pivot_strategy="none")


# =========================================================================
# GRUPO 3 — Captura de multiplicadores
# =========================================================================

class TestMultiplierCapture:

    def test_multipliers_2x2_simple(self):
        """A = [[2, 1], [4, 3]] con pivot_strategy='none'.
        Multiplicador esperado: L[1][0] = 4 / 2 = 2."""
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert len(gs.multipliers) == 1
        m = gs.multipliers[0]
        assert m["row"] == 1
        assert m["col"] == 0
        assert m["value"] == Fraction(2)

    def test_multipliers_3x3_multiple_eliminations(self):
        """A = [[2, 1, 1], [4, 3, 3], [6, 5, 7]].
        Eliminaciones esperadas:
          (1, 0): 4/2 = 2
          (2, 0): 6/2 = 3
          (2, 1): tras eliminar col 0, A[2][1] = 5 - 3·1 = 2;
                  pivote A[1][1] = 3 - 2·1 = 1 → 2/1 = 2
        """
        gs = GaussSolver(
            Matrix(3, 4, [
                ["2", "1", "1", "0"],
                ["4", "3", "3", "0"],
                ["6", "5", "7", "0"],
            ]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert len(gs.multipliers) == 3
        m_by_rc = {(m["row"], m["col"]): m["value"] for m in gs.multipliers}
        assert m_by_rc[(1, 0)] == Fraction(2)
        assert m_by_rc[(2, 0)] == Fraction(3)
        assert m_by_rc[(2, 1)] == Fraction(2)

    def test_multiplier_values_are_fractions(self):
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert all(isinstance(m["value"], Fraction) for m in gs.multipliers)

    def test_multiplier_with_fractional_values(self):
        """A = [[1/2, 1/3], [1/4, 1/5]].
        Multiplicador esperado: (1/4) / (1/2) = 1/2."""
        gs = GaussSolver(
            Matrix(2, 3, [[Fraction(1, 2), Fraction(1, 3), Fraction(0)],
                          [Fraction(1, 4), Fraction(1, 5), Fraction(0)]]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert len(gs.multipliers) == 1
        assert gs.multipliers[0]["value"] == Fraction(1, 2)

    def test_multiplier_preserves_large_denominator(self):
        """Multiplicador con denominador grande no se trunca."""
        # A = [[1001, 0], [1, 1]]. Multiplicador = 1 / 1001.
        gs = GaussSolver(
            Matrix(2, 3, [["1001", "0", "0"], ["1", "1", "0"]]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert len(gs.multipliers) == 1
        assert gs.multipliers[0]["value"] == Fraction(1, 1001)

    def test_zero_target_no_multiplier_captured(self):
        """A = [[2, 1], [0, 3]]: A[1][0] ya es cero, no hay multiplicador."""
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["0", "3", "0"]]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert gs.multipliers == []

    def test_multiplier_count_matches_elimination_steps(self):
        """Cada multiplicador capturado corresponde a un paso de eliminación."""
        gs = GaussSolver(
            Matrix(3, 4, [
                ["2", "1", "1", "0"],
                ["4", "3", "3", "0"],
                ["6", "5", "7", "0"],
            ]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        elimination_steps = [
            s for s in gs.steps if s["description"].startswith("Fila ")
        ]
        assert len(gs.multipliers) == len(elimination_steps)

    def test_multipliers_stay_empty_when_capture_off(self):
        """Sin capture_multipliers, no se guarda nada aunque
        pivot_strategy='none' esté activo."""
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            capture_multipliers=False,
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert gs.multipliers == []


# =========================================================================
# GRUPO 4 — Detección de pivotes cero sin pivoteo
# =========================================================================

class TestZeroPivotDetection:

    def test_no_zero_pivots_on_regular_matrix(self):
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert gs.zero_pivots == []

    def test_zero_pivot_detected_first_column(self):
        """A = [[0, 1], [1, 0]] sin pivoteo: pivote cero en col 0."""
        gs = GaussSolver(
            Matrix(2, 3, [["0", "1", "0"], ["1", "0", "0"]]),
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert 0 in gs.zero_pivots

    def test_zero_pivot_detected_after_elimination(self):
        """A = [[1, 1], [1, 1]]. Tras eliminar col 0, A[1][1] = 0.
        Con pivoteo parcial, Gauss buscaría pivote en otra fila.
        Con pivot_strategy='none', se marca el pivote cero en col 1."""
        gs = GaussSolver(
            Matrix(2, 3, [["1", "1", "0"], ["1", "1", "0"]]),
            pivot_strategy="none",
        )
        gs.solve_reduction()
        assert 1 in gs.zero_pivots

    def test_no_row_swap_when_pivot_strategy_none(self):
        """A = [[0, 1], [1, 0]] no debe intercambiar filas."""
        gs = GaussSolver(
            Matrix(2, 3, [["0", "1", "0"], ["1", "0", "0"]]),
            pivot_strategy="none",
        )
        gs.solve_reduction()
        for s in gs.steps:
            assert not s["description"].startswith("Intercambio")

    def test_row_swap_happens_with_partial(self):
        """A = [[0, 1], [1, 0]] con pivoteo parcial SÍ intercambia."""
        gs = GaussSolver(
            Matrix(2, 3, [["0", "1", "0"], ["1", "0", "0"]]),
            pivot_strategy="partial",
        )
        gs.solve_reduction()
        descriptions = [s["description"] for s in gs.steps]
        assert any(d.startswith("Intercambio") for d in descriptions)


# =========================================================================
# GRUPO 5 — Integración con solve_reduction
# =========================================================================

class TestSolveReductionIntegration:

    def test_solve_reduction_works_with_none_pivot(self):
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            pivot_strategy="none",
        )
        result = gs.solve_reduction()
        assert "reduced_matrix" in result
        assert result["rank"] == 2

    def test_reduced_matrix_matches_partial_when_no_swap_needed(self):
        """Sin swap necesario, pivot_strategy='none' y 'partial'
        producen la misma matriz reducida."""
        data = [
            ["2", "1", "0"],
            ["1", "2", "0"],
        ]
        gs_partial = GaussSolver(Matrix(2, 3, data), pivot_strategy="partial")
        gs_none = GaussSolver(Matrix(2, 3, data), pivot_strategy="none")
        r_partial = gs_partial.solve_reduction()
        r_none = gs_none.solve_reduction()
        assert r_partial["reduced_matrix"] == r_none["reduced_matrix"]
        assert r_partial["rank"] == r_none["rank"]
        assert r_partial["pivot_cols"] == r_none["pivot_cols"]


# =========================================================================
# GRUPO 6 — Gauss-Jordan hereda las extensiones
# =========================================================================

class TestGaussJordanInheritance:

    def test_gj_accepts_pivot_strategy_kwarg(self):
        gj = GaussJordanSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            pivot_strategy="none",
        )
        assert gj.pivot_strategy == "none"

    def test_gj_accepts_capture_multipliers(self):
        gj = GaussJordanSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        assert gj.capture_multipliers is True

    def test_gj_captures_multipliers_on_both_sides(self):
        """Gauss-Jordan elimina arriba Y debajo del pivote.
        Con capture_multipliers=True, captura ambos lados."""
        gj = GaussJordanSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            capture_multipliers=True,
            pivot_strategy="none",
        )
        gj.solve_reduction()
        # Elimina (1, 0) con factor 4/2 = 2;
        # luego en col 1 elimina (0, 1) con factor 1/1 = 1.
        assert len(gj.multipliers) == 2
        m_by_rc = {(m["row"], m["col"]): m["value"] for m in gj.multipliers}
        assert m_by_rc[(1, 0)] == Fraction(2)
        assert m_by_rc[(0, 1)] == Fraction(1)
        
    def test_normalize_pivots_default_is_true(self):
        """Default: los pivotes quedan en 1 (comportamiento histórico)."""
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            pivot_strategy="none",
        )
        result = gs.solve_reduction()
        assert result["reduced_matrix"].get(0, 0) == Fraction(1)
        assert result["reduced_matrix"].get(1, 1) == Fraction(1)

    def test_normalize_pivots_false_keeps_original_values(self):
        """Con normalize_pivots=False los pivotes conservan su valor original."""
        gs = GaussSolver(
            Matrix(2, 3, [["2", "1", "0"], ["4", "3", "0"]]),
            pivot_strategy="none",
            normalize_pivots=False,
        )
        result = gs.solve_reduction()
        assert result["reduced_matrix"].get(0, 0) == Fraction(2)
        assert result["reduced_matrix"].get(1, 1) == Fraction(1)