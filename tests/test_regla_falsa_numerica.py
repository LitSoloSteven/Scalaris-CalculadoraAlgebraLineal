"""Pruebas numericas del motor de regla falsa (regresion de capacidad)."""
import pytest

from src.backend.resolutores.raices.aritmetica_regla_falsa import (
    peso_escalado,
    punto_cruce,
)
from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.errores_numericos import ErrorCapacidadNumerica
from src.backend.resolutores.raices.regla_falsa import regla_falsa
from tests.test_regla_falsa_dominio import _entrada


def test_peso_escalado_normaliza_magnitudes_opuestas():
    """Regresion del bug: -1e308 / 1e308 no desborda; el peso debe ser 0.5."""
    assert peso_escalado(-1e308, 1e308) == 0.5


def test_peso_escalado_magnitudes_grandes_asimetricas():
    """Con magnitudes grandes distintas, t coincide con la formula exacta."""
    esperado = 1.0 / 1.3
    assert abs(peso_escalado(-1e308, 3e307) - esperado) < 1e-15


def test_peso_escalado_rechaza_ambos_cero():
    """Ambos extremos en cero no admiten interpolacion."""
    with pytest.raises(ErrorCapacidadNumerica) as info:
        peso_escalado(0.0, 0.0)
    assert getattr(info.value, "codigo", None) == "INTERPOLACION_NO_REPRESENTABLE"


@pytest.mark.parametrize("valor", [float("inf"), float("-inf"), float("nan")])
def test_peso_escalado_rechaza_escala_no_finita(valor):
    """Una escala NaN o infinita no es representable."""
    with pytest.raises(ErrorCapacidadNumerica) as info:
        peso_escalado(valor, 1.0)
    assert getattr(info.value, "codigo", None) == "INTERPOLACION_NO_REPRESENTABLE"


def test_punto_cruce_magnitudes_grandes_da_cero():
    """Combinacion convexa: c=0 con extremos -1e308 y 1e308."""
    assert punto_cruce(-1.0, 1.0, -1e308, 1e308) == 0.0


def test_punto_cruce_intervalo_asimetrico_mantiene_c_en_rango():
    """Con [0, 2] y magnitudes opuestas, c se mantiene en el intervalo."""
    c = punto_cruce(0.0, 2.0, -1e308, 1e308)
    assert 0.0 <= c <= 2.0
    assert abs(c - 1.0) < 1e-15


def test_punto_cruce_ancho_no_representable():
    """Intervalo -1e308 a 1e308 no tiene ancho representable."""
    with pytest.raises(ErrorCapacidadNumerica) as info:
        punto_cruce(-1e308, 1e308, -1.0, 1.0)
    assert getattr(info.value, "codigo", None) == "ANCHO_NO_REPRESENTABLE"
    
def test_escalado_1e308_no_desborda_y_encuentra_cero():
    """1e308*x en [-1,1]: primera aproximación en 0 sin desbordar (regresión R1)."""
    resultado = regla_falsa(_entrada("1e308*x", -1, 1))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_aproximacion"
    assert resultado.aproximacion == pytest.approx(0.0, abs=1e-12)


def test_escalado_1e_320_cero_interior_valido():
    """1e-320*x en [-1,1]: cero interior válido, sin subdesbordamiento."""
    resultado = regla_falsa(_entrada("1e-320*x", -1, 1))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_aproximacion"
    assert resultado.aproximacion == pytest.approx(0.0, abs=1e-12)


def test_1e_400_rechazado_por_subdesbordamiento():
    """1e-400*x es rechazado con SUBDESBORDAMIENTO al compilar el literal."""
    resultado = regla_falsa(_entrada("1e-400*x", -1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "SUBDESBORDAMIENTO"
    assert resultado.iteraciones == ()


def test_extremos_1e308_ancho_no_representable():
    """Extremos -1e308 y 1e308: ANCHO_NO_REPRESENTABLE, sin cifras infinitas."""
    resultado = regla_falsa(_entrada("x", -1e308, 1e308))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ANCHO_NO_REPRESENTABLE"
    assert resultado.iteraciones == ()
    assert resultado.aproximacion is None
    assert resultado.residuo is None
    
def test_lentitud_x10_limite_iteraciones_no_estancamiento():
    """x^10-1 en [0,2], límite 2: LIMITE_ITERACIONES, no estancamiento."""
    entrada = EntradaReglaFalsa(
        expresion="x^10-1",
        extremo_izquierdo=0.0,
        extremo_derecho=2.0,
        tolerancia=1e-12,
        limite_iteraciones=2,
    )
    resultado = regla_falsa(entrada)
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert resultado.motivo_parada == "limite_iteraciones"
    assert resultado.iteraciones_totales == 2
    assert all(fila.accion != "sin_cambio" for fila in resultado.iteraciones)


def test_tolerancia_estricta_no_cierra_por_igualdad():
    """x^2-2 en [0,2], tol 1, límite 1: residuo 1 no cumple < y da LIMITE_ITERACIONES."""
    entrada = EntradaReglaFalsa(
        expresion="x^2-2",
        extremo_izquierdo=0.0,
        extremo_derecho=2.0,
        tolerancia=1.0,
        limite_iteraciones=1,
    )
    resultado = regla_falsa(entrada)
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert resultado.aproximacion == pytest.approx(1.0)
    assert resultado.residuo == pytest.approx(1.0)


def test_convergencia_en_ultima_fila_es_exito():
    """x-1 en [0,2], límite 1: cierra por raíz en la única fila, no por límite."""
    entrada = EntradaReglaFalsa(
        expresion="x-1",
        extremo_izquierdo=0.0,
        extremo_derecho=2.0,
        tolerancia=1e-6,
        limite_iteraciones=1,
    )
    resultado = regla_falsa(entrada)
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_aproximacion"
    assert resultado.iteraciones_totales == 1


def test_oraculos_racionales_primeras_tres_filas():
    """x^2-2 en [1,2]: tres aproximaciones racionales consecutivas del manual."""
    from fractions import Fraction
    entrada = EntradaReglaFalsa(
        expresion="x^2-2",
        extremo_izquierdo=1.0,
        extremo_derecho=2.0,
        tolerancia=1e-20,
        limite_iteraciones=3,
    )
    resultado = regla_falsa(entrada)
    assert resultado.iteraciones_totales == 3
    esperados = [
        (Fraction(4, 3), Fraction(-2, 9)),
        (Fraction(7, 5), Fraction(-1, 25)),
        (Fraction(24, 17), Fraction(-2, 289)),
    ]
    for fila, (c_esperada, f_c_esperada) in zip(resultado.iteraciones, esperados):
        assert fila.aproximacion == pytest.approx(float(c_esperada), rel=1e-12)
        assert fila.valor_aproximacion == pytest.approx(float(f_c_esperada), rel=1e-12)


def test_referencia_9_filas_x_cuadrado_menos_dos():
    """x^2-2 en [1,2] con 9 iteraciones: c y residuo del manual, ambos bajo 1e-6."""
    import math
    entrada = EntradaReglaFalsa(
        expresion="x^2-2",
        extremo_izquierdo=1.0,
        extremo_derecho=2.0,
        tolerancia=1e-20,
        limite_iteraciones=9,
    )
    resultado = regla_falsa(entrada)
    assert resultado.iteraciones_totales == 9
    ultima = resultado.iteraciones[-1]
    assert abs(ultima.aproximacion - math.sqrt(2)) < 1e-6
    assert abs(ultima.residuo) < 1e-6