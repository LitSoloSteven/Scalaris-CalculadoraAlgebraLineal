"""Pruebas del motor de Newton-Raphson."""
import math

import pytest

from src.backend.resolutores.raices.newton_raphson import EntradaNewtonRaphson, newton_raphson


def _entrada(expresion="x^2 - 2", derivada="2*x", x0=1.5, tolerancia=1e-8, limite=100):
    return EntradaNewtonRaphson(
        expresion=expresion,
        derivada=derivada,
        aproximacion_inicial=x0,
        tolerancia=tolerancia,
        limite_iteraciones=limite,
    )


def test_newton_raphson_converge_a_raiz_de_dos():
    """La secuencia converge a la raíz positiva de x²−2."""
    resultado = newton_raphson(_entrada())
    assert resultado.estado == "EXITO"
    assert resultado.aproximacion == pytest.approx(math.sqrt(2), abs=1e-7)
    assert resultado.residuo < 1e-8
    assert resultado.iteraciones_totales == len(resultado.iteraciones)


def test_raiz_en_aproximacion_inicial():
    """Si f(x₀)=0 el resultado se devuelve sin iterar."""
    resultado = newton_raphson(_entrada("x - 3", "1", 3))
    assert resultado.estado == "EXITO"
    assert resultado.aproximacion == 3
    assert resultado.iteraciones_totales == 0


def test_derivada_cero_se_detecta():
    """Evita dividir entre cero cuando la derivada es nula."""
    resultado = newton_raphson(_entrada("x^2 + 1", "2*x", 0))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DERIVADA_CERO"


def test_limite_de_iteraciones_conserva_el_ultimo_punto():
    """El límite devuelve la última aproximación calculada."""
    resultado = newton_raphson(_entrada(limite=1, tolerancia=1e-15))
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert len(resultado.iteraciones) == 1
    assert resultado.aproximacion == resultado.iteraciones[-1].x_siguiente


def test_dominio_invalido_en_funcion():
    """Una función fuera de su dominio genera un diagnóstico de error."""
    resultado = newton_raphson(_entrada("sqrt(x)", "1/(2*sqrt(x))", -1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"


def test_derivada_fuera_de_dominio():
    """El motor también valida cada evaluación de la derivada."""
    resultado = newton_raphson(_entrada("x^2 + 1", "sqrt(x)", -1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"


def test_expresion_de_derivada_invalida():
    """La derivada usa la misma gramática segura que las funciones del proyecto."""
    resultado = newton_raphson(_entrada("x^2 - 2", "desconocida"))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "EXPRESION_INVALIDA"


def test_entrada_inicial_no_finita_se_rechaza():
    """Los datos iniciales deben ser reales y finitos."""
    resultado = newton_raphson(_entrada(x0=float("inf")))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"


def test_derivada_cero_despues_de_una_iteracion_conserva_la_traza():
    """Si la derivada se anula en el nuevo punto, conserva la iteración anterior."""
    resultado = newton_raphson(_entrada("x^2 + 1", "2*x", 1, tolerancia=1e-15))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DERIVADA_CERO"
    assert resultado.iteraciones_totales == 1
    assert resultado.aproximacion == 0
    assert resultado.iteraciones[0].x_siguiente == 0
