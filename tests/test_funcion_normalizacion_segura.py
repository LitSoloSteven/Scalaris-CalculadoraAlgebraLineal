"""Equivalencia matemática y precedencias de la normalización léxica segura."""
import ast
import math

import pytest

from src.backend.excepciones import ErrorNoFinito
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar
from src.backend.resolutores.raices.gramatica_funcion import analizar_expresion
from src.backend.resolutores.raices.normalizacion_funcion import normalizar_expresion


@pytest.mark.parametrize("expresion, explicita", [
    ("2x", "2*x"), ("3sin(x)", "3*sin(x)"), ("2(x+1)", "2*(x+1)"),
    ("(x+1)(x-1)", "(x+1)*(x-1)"), ("(x+1)sin(x)", "(x+1)*sin(x)"),
    ("sin(x)cos(x)", "sin(x)*cos(x)"), ("(x+1)2", "(x+1)*2"),
    ("2pi x", "2*pi*x"), ("x−2", "x-2"), ("x²+x³", "x**2+x**3"),
    ("−x²", "-(x**2)"), ("(-x)²", "(-x)**2"), ("e^-x", "e**(-x)"),
    ("2^-x²", "2**(-(x**2))"), ("2^3^2", "2**(3**2)"),
    ("8/2(x+1)", "8/2*(x+1)"), ("x²³", "x**23"),
    ("1e-200(x-1)", "1e-200*(x-1)"), ("1e−200x", "1e-200*x"),
    (".5x+2.5E+1", ".5*x+2.5E+1"), ("2**-x", "2**(-x)"),
    ("(x\n+1)", "x+1"),
])
def test_equivalencia_y_precedencia(expresion, explicita):
    """La notación ampliada equivale a operadores explícitos en puntos positivos y negativos."""
    funcion, referencia = compilar(expresion), compilar(explicita)
    for valor in (-1.25, 0, 1.5):
        assert evaluar(funcion, valor) == evaluar(referencia, valor)
    normalizada = normalizar_expresion(expresion)
    assert normalizar_expresion(normalizada) == normalizada


@pytest.mark.parametrize("expresion, esperado", [
    ("ln(e)", 1), ("log(e)", 1), ("log10(100)", 2), ("log2(8)", 3),
    ("asin(.5)", math.asin(.5)), ("acos(.5)", math.acos(.5)),
    ("atan(1)", math.pi / 4), ("sinh(1)", math.sinh(1)),
    ("cosh(1)", math.cosh(1)), ("tanh(1)", math.tanh(1)),
])
def test_catalogo_real_en_radianes(expresion, esperado):
    """El catálogo nuevo conserva los valores de math sin conversión angular implícita."""
    assert evaluar(compilar(expresion), 0) == pytest.approx(esperado)


def test_literales_cientificos_son_un_solo_numero():
    """Los signos del exponente no se transforman en sumas, restas o productos por e."""
    arbol = analizar_expresion("1e-200x + 2E+10")
    literales = [nodo.value for nodo in ast.walk(arbol) if isinstance(nodo, ast.Constant)]
    assert literales == [2e10, 1e-200]
    assert evaluar(compilar("1e-200x"), 2) == 2e-200


@pytest.mark.parametrize("expresion", ["1e-400x", "0.0001e-400(x+1)", "1e-200x²*1e-200"])
def test_subdesbordamiento_no_se_convierte_en_raiz(expresion):
    """La normalización conserva la detección de literales y productos que pierden su valor."""
    with pytest.raises(ErrorNoFinito) as fallo:
        evaluar(compilar(expresion), 2)
    assert fallo.value.codigo == "SUBDESBORDAMIENTO"
