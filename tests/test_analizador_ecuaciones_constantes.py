"""Interpretación de ecuaciones constantes dentro de sistemas lineales."""
from fractions import Fraction
from src.backend.utils.parsers import SystemParser
from src.backend.solvers.linear_systems.gauss import GaussSolver


def test_ecuacion_constante_conserva_fila_incompatible():
    """La igualdad entre cero y un valor no nulo genera la fila correspondiente."""
    texto = "x + y = 3\n0 = 5"
    valido, matriz, variables, mensaje = SystemParser.parse_system(texto)
    assert valido, mensaje
    assert variables == ["x", "y"]
    assert matriz.rows == 2
    assert matriz.cols == 3
    assert matriz.get(0, 0) == Fraction(1)
    assert matriz.get(0, 1) == Fraction(1)
    assert matriz.get(0, 2) == Fraction(3)
    assert matriz.get(1, 0) == Fraction(0)
    assert matriz.get(1, 1) == Fraction(0)
    assert matriz.get(1, 2) == Fraction(5)


def test_ecuacion_constante_incompatible_produce_sistema_sin_solucion():
    """El resolutor detecta la incompatibilidad de la fila constante."""
    texto = "x + y = 3\n0 = 5"
    valido, matriz, _, _ = SystemParser.parse_system(texto)
    assert valido
    resultado = GaussSolver(matriz).solve()
    assert resultado["status"] == "NO_SOLUTION"


def test_identidad_constante_produce_fila_nula():
    """La igualdad cero a cero conserva una fila válida de ceros."""
    texto = "x = 1\n0 = 0"
    valido, matriz, _, mensaje = SystemParser.parse_system(texto)
    assert valido, mensaje
    assert matriz.get(1, 0) == Fraction(0)
    assert matriz.get(1, 1) == Fraction(0)


def test_sistema_sin_variables_se_rechaza():
    """Una colección puramente constante no se interpreta como sistema de variables."""
    valido, _, _, mensaje = SystemParser.parse_system("0 = 5")
    assert not valido
    assert "variable" in mensaje.lower()


def test_constante_izquierda_se_traslada_al_independiente():
    """La constante izquierda se resta del término independiente."""
    texto = "x = 1\n5 = 3"
    valido, matriz, _, mensaje = SystemParser.parse_system(texto)
    assert valido, mensaje
    assert matriz.get(1, 0) == Fraction(0)
    assert matriz.get(1, 1) == Fraction(-2)
