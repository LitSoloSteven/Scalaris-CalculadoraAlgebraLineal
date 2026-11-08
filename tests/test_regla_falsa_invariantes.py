"""Invariantes que toda traza cerrada de regla falsa debe cumplir."""
import json
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.regla_falsa import regla_falsa


def _entrada(expresion="x^2-2", a=1.0, b=2.0, tol=1e-6, limite=100):
    return EntradaReglaFalsa(
        expresion=expresion,
        extremo_izquierdo=a,
        extremo_derecho=b,
        tolerancia=tol,
        limite_iteraciones=limite,
    )


def _casos():
    return [
        _entrada("x^2-2", 1, 2),
        _entrada("x-1", 0, 2),
        _entrada("x^2+1", -1, 1),                 # SIN_CAMBIO_DE_SIGNO, sin filas
        _entrada("1e-320*x", -1, 1),
        _entrada("1e-400*x", -1, 1),              # ERROR de sintaxis, sin filas
        _entrada("x^2-2", 1, 2, limite=1),
        _entrada("x^2-2", 1, 2, limite=9),
    ]


@pytest.mark.parametrize("entrada", _casos())
def test_indices_consecutivos_desde_uno(entrada):
    """La i de cada fila empieza en 1 y avanza de uno en uno."""
    resultado = regla_falsa(entrada)
    for esperado, fila in enumerate(resultado.iteraciones, start=1):
        assert fila.i == esperado


@pytest.mark.parametrize("entrada", _casos())
def test_residuo_coincide_con_abs_aproximacion(entrada):
    """El residuo publicado es exactamente abs(valor_aproximacion)."""
    resultado = regla_falsa(entrada)
    for fila in resultado.iteraciones:
        assert fila.residuo == abs(fila.valor_aproximacion)


@pytest.mark.parametrize("entrada", _casos())
def test_intervalo_siguiente_contenido_en_el_anterior(entrada):
    """El intervalo siguiente está contenido en el anterior (o coincide si hay estancamiento)."""
    resultado = regla_falsa(entrada)
    for fila in resultado.iteraciones:
        a, b = fila.extremo_izquierdo, fila.extremo_derecho
        c, d = fila.intervalo_siguiente
        assert a <= c <= d <= b


@pytest.mark.parametrize("entrada", _casos())
def test_accion_coherente_con_signo(entrada):
    """La acción registrada coincide con el signo del producto o con estancamiento."""
    resultado = regla_falsa(entrada)
    for fila in resultado.iteraciones:
        if fila.accion == "raiz":
            assert fila.signo_producto == 0
        elif fila.accion == "reemplazar_b":
            assert fila.signo_producto == -1
        elif fila.accion == "reemplazar_a":
            assert fila.signo_producto == 1
        elif fila.accion == "sin_cambio":
            assert fila.intervalo_siguiente == (fila.extremo_izquierdo, fila.extremo_derecho)


@pytest.mark.parametrize("entrada", _casos())
def test_iteraciones_totales_coincide_con_len(entrada):
    """iteraciones_totales refleja el número real de filas."""
    resultado = regla_falsa(entrada)
    assert resultado.iteraciones_totales == len(resultado.iteraciones)


@pytest.mark.parametrize("entrada", _casos())
def test_intervalo_final_coincide_con_ultima_fila(entrada):
    """El intervalo_final es exactamente el intervalo_siguiente de la última fila."""
    resultado = regla_falsa(entrada)
    if resultado.iteraciones:
        assert resultado.intervalo_final == resultado.iteraciones[-1].intervalo_siguiente


@pytest.mark.parametrize("entrada", _casos())
def test_resultado_serializable_sin_nan(entrada):
    """Todos los campos numéricos del resultado son finitos y serializables."""
    resultado = regla_falsa(entrada)
    json.dumps(asdict(resultado), allow_nan=False)