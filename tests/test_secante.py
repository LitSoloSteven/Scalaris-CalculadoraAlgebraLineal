"""Pruebas del motor del método abierto de la secante."""
import math

import pytest

from src.backend.resolutores.raices.secante import EntradaSecante, secante


def _entrada(expresion="x^2 - 2", x0=1, x1=2, tolerancia=1e-8, limite=100, unidad="radianes"):
    return EntradaSecante(
        expresion=expresion,
        x_anterior=x0,
        x_actual=x1,
        tolerancia=tolerancia,
        limite_iteraciones=limite,
        unidad_angular=unidad,
    )


def test_secante_converge_a_raiz_de_dos():
    """La secante aproxima sqrt(2) sin derivada."""
    resultado = secante(_entrada())
    assert resultado.estado == "EXITO"
    assert resultado.aproximacion == pytest.approx(math.sqrt(2), abs=1e-7)
    assert resultado.residuo < 1e-8
    assert resultado.iteraciones_totales == len(resultado.iteraciones)


def test_secante_no_exige_cambio_de_signo():
    """Dos puntos con el mismo signo pueden converger a una raíz."""
    resultado = secante(_entrada("x^2 - 2", 2, 3))
    assert resultado.estado == "EXITO"
    assert resultado.aproximacion == pytest.approx(math.sqrt(2), abs=1e-7)


def test_denominador_cero_se_informa_sin_dividir():
    """Cuando las evaluaciones coinciden, el motor detiene el método."""
    resultado = secante(_entrada("x^2 + 1", -1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DENOMINADOR_CERO"
    assert resultado.iteraciones == ()


def test_raiz_en_una_aproximacion_inicial():
    """Una aproximación inicial que ya es raíz no requiere iteraciones."""
    resultado = secante(_entrada("x - 3", 3, 4))
    assert resultado.estado == "EXITO"
    assert resultado.aproximacion == 3
    assert resultado.iteraciones_totales == 0


def test_limite_de_iteraciones_conserva_la_ultima_aproximacion():
    """El límite devuelve el último valor calculado y su residuo."""
    resultado = secante(_entrada(limite=1, tolerancia=1e-15))
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert len(resultado.iteraciones) == 1
    assert resultado.aproximacion == resultado.iteraciones[-1].x_siguiente
    assert resultado.residuo == pytest.approx(abs(resultado.iteraciones[-1].f_siguiente))


def test_funcion_fuera_de_dominio_devuelve_error():
    """La evaluación inicial de sqrt(x) falla si se inicia con un negativo."""
    resultado = secante(_entrada("sqrt(x)", -1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"


def test_unidad_angular_en_grados():
    """El evaluador compartido permite resolver funciones trigonométricas en grados."""
    resultado = secante(_entrada("sin(x) - 0.5", 10, 40, unidad="grados"))
    assert resultado.estado == "EXITO"
    assert resultado.aproximacion == pytest.approx(30, abs=1e-5)


def test_aproximaciones_iniciales_iguales_se_rechazan():
    """La secante necesita dos valores iniciales diferentes."""
    resultado = secante(_entrada("x^2 - 2", 1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"


@pytest.mark.parametrize("expresion", ["sin()", "__import__('os')", "x + unknown"])
def test_expresiones_no_permitidas_no_se_ejecutan(expresion):
    """Solo se acepta la gramática matemática segura del proyecto."""
    resultado = secante(_entrada(expresion))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "EXPRESION_INVALIDA"
