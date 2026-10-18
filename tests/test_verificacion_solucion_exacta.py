"""Verificación de soluciones racionales y errores de celda."""
from fractions import Fraction
from src.backend.utilidades.validadores import ValidadorMatriz


def test_verificacion_acepta_fraccion_exacta():
    """Una solución racional exacta satisface la ecuación."""
    valido, _ = ValidadorMatriz.verificar_solucion([[Fraction(1001)]], [Fraction(1, 1001)], [Fraction(1)])
    assert valido


def test_verificacion_rechaza_aproximacion():
    """Una aproximación cercana no satisface la igualdad racional."""
    valido, informe = ValidadorMatriz.verificar_solucion([[Fraction(1)]], [Fraction(1, 1000)], [Fraction(1, 1001)])
    assert not valido
    assert "Incorrecto" in informe[0]


def test_verificacion_interpreta_cadenas_exactamente():
    """Las entradas textuales conservan la igualdad exacta."""
    valido, _ = ValidadorMatriz.verificar_solucion([["1001"]], ["1/1001"], ["1"])
    assert valido


def test_verificacion_acepta_fracciones_simples():
    """La suma de productos racionales verifica el término independiente."""
    valido, _ = ValidadorMatriz.verificar_solucion(
        [[Fraction(2), Fraction(3)]], [Fraction(1, 2), Fraction(1, 3)], [Fraction(2)])
    assert valido


def test_verificacion_rechaza_solucion_incorrecta():
    """El informe identifica una igualdad incumplida."""
    valido, informe = ValidadorMatriz.verificar_solucion([[Fraction(1)]], [Fraction(5)], [Fraction(3)])
    assert not valido
    assert "Incorrecto" in informe[0]


def test_verificacion_identifica_celda_invalida_en_coeficientes():
    """El error conserva la coordenada de la matriz de coeficientes."""
    valido, informe = ValidadorMatriz.verificar_solucion([["abc"]], [Fraction(1)], [Fraction(1)])
    assert not valido
    assert "A[1,1]" in informe[0]


def test_verificacion_identifica_celda_invalida_en_solucion():
    """El error conserva el índice del vector solución."""
    valido, informe = ValidadorMatriz.verificar_solucion([[Fraction(1)]], ["xyz"], [Fraction(1)])
    assert not valido
    assert "x[1]" in informe[0]


def test_verificacion_identifica_celda_invalida_en_independientes():
    """El error conserva el índice del término independiente."""
    valido, informe = ValidadorMatriz.verificar_solucion([[Fraction(1)]], [Fraction(1)], ["oops"])
    assert not valido
    assert "b[1]" in informe[0]


def test_verificacion_latex_muestra_fraccion_exacta():
    """El detalle LaTeX mantiene numerador y denominador."""
    valido, informe = ValidadorMatriz.verificar_solucion([[Fraction(7)]], ["9/7"], [Fraction(9)], como_latex=True)
    assert valido
    assert r"\frac{9}{7}" in informe[0]


def test_verificacion_textual_muestra_fraccion_exacta():
    """El detalle textual conserva la fracción completa."""
    valido, informe = ValidadorMatriz.verificar_solucion([[Fraction(7)]], [Fraction(9, 7)], [Fraction(9)], como_latex=False)
    assert valido
    assert "9/7" in informe[0]
