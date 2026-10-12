"""Precisión de literales decimales en productos matriciales."""
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def _producto_escalar(token: str, valor_matricial: Fraction) -> Fraction:
    evaluador = MatrixExpressionEvaluator()
    matriz_a = Matrix(1, 1, [[valor_matricial]])
    resultado = evaluador.evaluate(f"{token}A", {"A": matriz_a})
    assert resultado["status"] == "SUCCESS", resultado.get("message")
    return resultado["result_matrix"].data[0][0]


def test_decimal_muy_pequeno_conserva_valor_no_nulo():
    """El decimal pequeño no se trunca a cero."""
    resultado = _producto_escalar("0.0000001", Fraction(1))
    assert resultado == Fraction(1, 10_000_000)


def test_decimal_de_pi_conserva_fraccion_exacta():
    """Todos los dígitos escritos participan en la fracción exacta."""
    resultado = _producto_escalar("3.14159265", Fraction(1))
    assert resultado == Fraction(62831853, 20_000_000)


def test_decimal_simple_conserva_fraccion_exacta():
    """El decimal medio se representa como un medio."""
    resultado = _producto_escalar("0.5", Fraction(1))
    assert resultado == Fraction(1, 2)


def test_literal_entero_conserva_valor_exacto():
    """El entero se conserva como valor racional exacto."""
    resultado = _producto_escalar("5", Fraction(1))
    assert resultado == Fraction(5)


def test_literal_conserva_denominador_grande():
    """El decimal largo conserva el denominador de su representación racional."""
    resultado = _producto_escalar("0.000001234", Fraction(1))
    assert resultado == Fraction(1234, 1_000_000_000)
