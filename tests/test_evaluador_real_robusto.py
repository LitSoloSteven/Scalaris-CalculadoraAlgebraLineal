"""Validación de gramática real, capacidad numérica y dominios estructurales."""
import math

import pytest

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar


@pytest.mark.parametrize("expresion", ["sin()", "pi(1)", "sin", "sin(x, x)", "log(x, 10)",
    "sqrt(x=1)", "True", "'texto'", "1j", "[x]", "x.real", "__import__('os')", "lambda: x"])
def test_gramatica_invalida_no_se_compila(expresion):
    """Rechaza entradas que podrían producir tipos inesperados o ejecución arbitraria."""
    with pytest.raises(ValueError):
        compilar(expresion)


@pytest.mark.parametrize("expresion", ["1e-400", "exp(-1000)", "1e-300*1e-100", "1e-300/1e100", "1e-200**2"])
def test_subdesbordamiento_no_se_confunde_con_cero(expresion):
    """Devuelve un diagnóstico estable si una magnitud no nula se convierte en cero."""
    with pytest.raises(ErrorNoFinito) as fallo:
        evaluar(compilar(expresion), 0)
    assert fallo.value.codigo == "SUBDESBORDAMIENTO"


@pytest.mark.parametrize("expresion", ["(-1)**0.5", "sqrt(-1)", "log(0)", "0**-1", "1/0"])
def test_dominio_invalido_usa_excepcion_de_dominio(expresion):
    """No propaga TypeError ni ZeroDivisionError del evaluador al consumidor."""
    with pytest.raises(ErrorDominio):
        evaluar(compilar(expresion), 0)


@pytest.mark.parametrize("expresion", ["1e309", "exp(1000)", "1e308*1e308", "(1e308+1e308)-1e308"])
def test_no_finitos_intermedios_se_rechazan(expresion):
    """Impide que un desbordamiento intermedio se oculte en una expresión posterior."""
    with pytest.raises(ErrorNoFinito):
        evaluar(compilar(expresion), 0)


@pytest.mark.parametrize("expresion", ["1/x", "1/(x-0.1234)", "(x-1)/(x-0.1234)", "1/((x-0.1234)**2)", "(x-0.1234)**-2"])
def test_polos_afines_y_factores_se_detectan(expresion):
    """Localiza denominadores nulos aun sin evaluarlos exactamente durante la partición."""
    with pytest.raises(ErrorDominio) as fallo:
        comprobar_dominio_intervalo(expresion, (-1, 1))
    assert fallo.value.codigo == "SINGULARIDAD_DETECTADA"


def test_no_rechaza_denominador_cuadratico_positivo():
    """No interpreta dependencia no afín como una singularidad probada."""
    comprobar_dominio_intervalo("1/(x**2+1)", (-1, 1))
    assert evaluar(compilar("1/(x**2+1)"), 0) == 1


def test_ceros_legitimos_y_constantes_permitidas():
    """Conserva ceros algebraicos y las constantes del catálogo real."""
    assert evaluar(compilar("x-x + 0*x + 0**2"), 1) == 0
    assert evaluar(compilar("sin(x)+pi-e"), 0) == math.pi - math.e


def test_limites_de_expresion_y_argumento():
    """Acota longitud y profundidad y exige una abscisa real finita."""
    with pytest.raises(ValueError):
        compilar("1+" * 256 + "1")
    with pytest.raises(ValueError):
        compilar("sin(" * 34 + "x" + ")" * 34)
    with pytest.raises(ErrorNoFinito):
        evaluar(compilar("x"), math.inf)
