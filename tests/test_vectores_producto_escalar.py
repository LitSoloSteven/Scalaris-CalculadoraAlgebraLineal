"""Producto escalar de vectores, precisión y trazabilidad."""
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.operations import VectorOpsSolver


def test_producto_escalar_columna():
    """Un entero multiplica todas las componentes de la columna."""
    vector = Matrix(3, 1, [[2], [4], [6]])
    resultado = VectorOpsSolver().scalar_multiply(3, vector)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[6], [12], [18]]


def test_producto_escalar_fila():
    """El producto conserva la orientación de la fila."""
    vector = Matrix(1, 3, [[1, 2, 3]])
    resultado = VectorOpsSolver().scalar_multiply(2, vector)
    assert resultado["result_matrix"].data == [[2, 4, 6]]
    assert resultado["result_matrix"].rows == 1


def test_producto_escalar_fraccion():
    """El factor racional conserva componentes exactas."""
    vector = Matrix(3, 1, [[1], [2], [3]])
    resultado = VectorOpsSolver().scalar_multiply(Fraction(1, 2), vector)
    assert resultado["result_matrix"].data == [[Fraction(1, 2)], [1], [Fraction(3, 2)]]


def test_producto_escalar_cadena_racional_exacta():
    """Un factor escrito como fracción se interpreta exactamente."""
    vector = Matrix(2, 1, [[4], [8]])
    resultado = VectorOpsSolver().scalar_multiply("3/4", vector)
    assert resultado["result_matrix"].data == [[3], [6]]


def test_producto_escalar_cero():
    """El factor cero anula todas las componentes."""
    vector = Matrix(3, 1, [[1], [2], [3]])
    resultado = VectorOpsSolver().scalar_multiply(0, vector)
    assert resultado["result_matrix"].data == [[0], [0], [0]]


def test_producto_escalar_negativo():
    """El factor negativo invierte los signos correctamente."""
    vector = Matrix(2, 1, [[1], [-2]])
    resultado = VectorOpsSolver().scalar_multiply(-1, vector)
    assert resultado["result_matrix"].data == [[-1], [2]]


def test_producto_escalar_rechaza_factor_invalido():
    """Una cadena no numérica devuelve un error explicativo."""
    vector = Matrix(2, 1, [[1], [2]])
    resultado = VectorOpsSolver().scalar_multiply("abc", vector)
    assert resultado["status"] == "ERROR"
    assert "Escalar inválido" in resultado["message"]


def test_producto_escalar_rechaza_matriz_no_vectorial():
    """El producto vectorial no acepta una matriz rectangular."""
    vector = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = VectorOpsSolver().scalar_multiply(2, vector)
    assert resultado["status"] == "ERROR"
    assert "se esperaba un vector" in resultado["message"]


def test_producto_escalar_registra_paso_inicial_y_componentes():
    """Tres componentes producen cuatro pasos con el estado inicial."""
    vector = Matrix(3, 1, [[1], [2], [3]])
    resultado = VectorOpsSolver().scalar_multiply(2, vector)
    assert len(resultado["steps"]) == 4
