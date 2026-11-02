"""Pruebas unitarias para el evaluador seguro de funciones."""
import math
import pytest
from src.backend.excepciones import ErrorDominio
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar


def test_expresion_valida():
    """Evalúa un polinomio básico en un punto conocido."""
    f = compilar("x**2 - 2")
    assert evaluar(f, 1.5) == 0.25


def test_funciones_permitidas():
    """Evalúa funciones trigonométricas de la whitelist."""
    f = compilar("sin(x) + cos(x)")
    assert math.isclose(evaluar(f, 0), 1.0, rel_tol=1e-9)


def test_division_por_cero():
    """Rechaza la evaluación en una singularidad conocida."""
    f = compilar("1/x")
    with pytest.raises(ErrorDominio):
        evaluar(f, 0)


def test_logaritmo_negativo():
    """Rechaza dominio inválido para el logaritmo."""
    f = compilar("log(x)")
    with pytest.raises(ErrorDominio):
        evaluar(f, -1)


def test_codigo_no_permitido():
    """Rechaza código arbitrario en la expresión."""
    with pytest.raises(ValueError):
        compilar("__import__('os').system('ls')")