"""Formato exacto de los informes de verificación de soluciones."""
from fractions import Fraction
from src.backend.utilidades.validadores import ValidadorMatriz


def test_informe_latex_conserva_fracciones_exactas():
    """La comprobación muestra la fracción sin expandir el decimal."""
    coeficientes, solucion, independientes = [[Fraction(7)]], ["9/7"], [Fraction(9)]
    valido, informe = ValidadorMatriz.verificar_solucion(coeficientes, solucion, independientes, como_latex=True)
    assert valido
    assert r"\frac{9}{7}" in informe[0]
    assert "1.2857" not in informe[0]


def test_informe_textual_conserva_fracciones_exactas():
    """La representación textual tampoco aproxima la fracción."""
    coeficientes, solucion, independientes = [[Fraction(7)]], [Fraction(9, 7)], [Fraction(9)]
    valido, informe = ValidadorMatriz.verificar_solucion(coeficientes, solucion, independientes, como_latex=False)
    assert valido
    assert "9/7" in informe[0]
    assert "1.2857" not in informe[0]


def test_formato_conserva_verificacion_correcta():
    """El formato de salida conserva la verificación de la igualdad."""
    coeficientes = [[Fraction(1), Fraction(1)]]
    solucion, independientes = ["1/2", "1/2"], [Fraction(1)]
    valido, _ = ValidadorMatriz.verificar_solucion(coeficientes, solucion, independientes)
    assert valido


def test_informe_identifica_valores_incorrectos():
    """La solución que incumple la igualdad se informa como incorrecta."""
    coeficientes, solucion, independientes = [[Fraction(1)]], ["1/2"], [Fraction(9)]
    valido, informe = ValidadorMatriz.verificar_solucion(coeficientes, solucion, independientes)
    assert not valido
    assert "Incorrecto" in informe[0]


def test_informe_muestra_entero_sin_parte_decimal():
    """La suma entera aparece como entero en el informe."""
    coeficientes = [[Fraction(1), Fraction(1)]]
    solucion, independientes = ["1", "1"], [Fraction(2)]
    valido, informe = ValidadorMatriz.verificar_solucion(coeficientes, solucion, independientes)
    assert valido
    assert "= 2 " in informe[0] or "= 2  " in informe[0]
    assert "= 2.0" not in informe[0]
