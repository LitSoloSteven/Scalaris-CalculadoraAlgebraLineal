"""Precedencia del signo negativo en expresiones matriciales."""
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def test_menos_unario_despues_de_producto():
    """El signo de la segunda matriz se aplica antes del producto."""
    izquierda = Matrix(1, 1, [[2]])
    derecha = Matrix(1, 1, [[3]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("A*-B", {"A": izquierda, "B": derecha})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(-6)


def test_doble_menos_unario():
    """Dos signos negativos consecutivos conservan el valor original."""
    matriz = Matrix(1, 1, [[5]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("--A", {"A": matriz})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(5)


def test_menos_unario_al_inicio():
    """Un signo negativo inicial invierte el valor de la matriz."""
    matriz = Matrix(1, 1, [[7]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("-A", {"A": matriz})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(-7)


def test_menos_unario_entre_parentesis():
    """Los paréntesis conservan el signo negativo de la matriz."""
    matriz = Matrix(1, 1, [[3]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("(-A)", {"A": matriz})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(-3)
