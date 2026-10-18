"""Producto escalar de vectores, precisión y trazabilidad."""
from fractions import Fraction
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores


def test_producto_escalar_columna():
    """Un entero multiplica todas las componentes de la columna."""
    vector = Matriz(3, 1, [[2], [4], [6]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar(3, vector)
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos == [[6], [12], [18]]


def test_producto_escalar_fila():
    """El producto conserva la orientación de la fila."""
    vector = Matriz(1, 3, [[1, 2, 3]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar(2, vector)
    assert resultado["matriz_resultado"].datos == [[2, 4, 6]]
    assert resultado["matriz_resultado"].filas == 1


def test_producto_escalar_fraccion():
    """El factor racional conserva componentes exactas."""
    vector = Matriz(3, 1, [[1], [2], [3]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar(Fraction(1, 2), vector)
    assert resultado["matriz_resultado"].datos == [[Fraction(1, 2)], [1], [Fraction(3, 2)]]


def test_producto_escalar_cadena_racional_exacta():
    """Un factor escrito como fracción se interpreta exactamente."""
    vector = Matriz(2, 1, [[4], [8]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar("3/4", vector)
    assert resultado["matriz_resultado"].datos == [[3], [6]]


def test_producto_escalar_cero():
    """El factor cero anula todas las componentes."""
    vector = Matriz(3, 1, [[1], [2], [3]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar(0, vector)
    assert resultado["matriz_resultado"].datos == [[0], [0], [0]]


def test_producto_escalar_negativo():
    """El factor negativo invierte los signos correctamente."""
    vector = Matriz(2, 1, [[1], [-2]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar(-1, vector)
    assert resultado["matriz_resultado"].datos == [[-1], [2]]


def test_producto_escalar_rechaza_factor_invalido():
    """Una cadena no numérica devuelve un error explicativo."""
    vector = Matriz(2, 1, [[1], [2]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar("abc", vector)
    assert resultado["estado"] == "ERROR"
    assert "Escalar inválido" in resultado["mensaje"]


def test_producto_escalar_rechaza_matriz_no_vectorial():
    """El producto vectorial no acepta una matriz rectangular."""
    vector = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar(2, vector)
    assert resultado["estado"] == "ERROR"
    assert "se esperaba un vector" in resultado["mensaje"]


def test_producto_escalar_registra_paso_inicial_y_componentes():
    """Tres componentes producen cuatro pasos con el estado inicial."""
    vector = Matriz(3, 1, [[1], [2], [3]])
    resultado = ResolutorOperacionesVectores().multiplicar_escalar(2, vector)
    assert len(resultado["pasos"]) == 4
