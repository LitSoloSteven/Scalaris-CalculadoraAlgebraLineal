"""Tipos racionales y validación de resultados de expresiones matriciales."""
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def test_literal_conserva_precision_racional():
    """El producto de tres por un tercio produce un entero exacto."""
    matriz_a = Matrix(1, 1, [[Fraction(1, 3)]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("3A", {"A": matriz_a})
    valor = resultado["result_matrix"].get(0, 0)
    assert valor == Fraction(1, 1), f"Esperado Fraction(1), obtenido {valor!r}"
    assert isinstance(valor, Fraction), f"Tipo esperado Fraction, obtenido {type(valor).__name__}"


def test_producto_escalar_conserva_tipos_racionales():
    """Cada celda del producto conserva su valor y tipo racional."""
    matriz_b = Matrix(2, 2, [[1, 2], [3, 4]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("2B", {"B": matriz_b})
    assert resultado["status"] == "SUCCESS"
    esperado = [[Fraction(2), Fraction(4)], [Fraction(6), Fraction(8)]]
    for i in range(2):
        for j in range(2):
            obtenido = resultado["result_matrix"].get(i, j)
            assert obtenido == esperado[i][j], f"[{i},{j}]: esperado {esperado[i][j]}, obtenido {obtenido}"
            assert isinstance(obtenido, Fraction), f"[{i},{j}]: se esperaba Fraction, es {type(obtenido).__name__}"


def test_suma_matricial_conserva_tipos_racionales():
    """Cada celda de la suma mantiene la igualdad racional."""
    matriz_a = Matrix(2, 2, [[1, 0], [0, 1]])
    matriz_b = Matrix(2, 2, [[1, 2], [3, 4]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("A3 + B3", {"A3": matriz_a, "B3": matriz_b})
    assert resultado["status"] == "SUCCESS"
    esperado = [[Fraction(2), Fraction(2)], [Fraction(3), Fraction(5)]]
    for i in range(2):
        for j in range(2):
            obtenido = resultado["result_matrix"].get(i, j)
            assert obtenido == esperado[i][j], f"[{i},{j}]: esperado {esperado[i][j]}, obtenido {obtenido}"


def test_expresion_escalar_pura_se_rechaza():
    """La expresión que no devuelve matriz conserva el error explicativo."""
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("3 * 4", {})
    assert resultado["status"] == "ERROR"
    assert "escalar" in resultado["message"].lower()


def test_negacion_unaria_conserva_fraccion():
    """La negación cambia el signo sin aproximar la celda."""
    matriz_c = Matrix(1, 1, [[Fraction(1, 3)]])
    evaluador = MatrixExpressionEvaluator()
    resultado = evaluador.evaluate("-C", {"C": matriz_c})
    valor = resultado["result_matrix"].get(0, 0)
    assert valor == Fraction(-1, 3), f"Esperado Fraction(-1/3), obtenido {valor!r}"
    assert isinstance(valor, Fraction), f"Tipo esperado Fraction, obtenido {type(valor).__name__}"
