"""Regresiones de los requisitos numéricos y del contrato completo de bisección."""
import json
import math
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.aritmetica_biseccion import punto_medio, error_relativo_numerico
from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion


def entrada(expresion="x**2-2", intervalo=(1.0, 2.0), decimales=4, limite=100):
    """Construye una entrada directa para ejercitar validación y cálculo del dominio."""
    return EntradaBiseccion(expresion, *intervalo, decimales, limite)


def test_estancamiento_conserva_traza_y_no_repite_hasta_limite():
    """La falta de resolución se diagnostica al coincidir el medio con un extremo."""
    resultado = biseccion(entrada("sin(x)", (1e16, 1e16 + 4), 15))
    assert resultado.estado == "PRECISION_NO_ALCANZADA"
    assert resultado.motivo_parada == "estancamiento"
    assert resultado.codigo_diagnostico == "ESTANCAMIENTO"
    assert len(resultado.iteraciones) < 100
    assert resultado.aproximacion == resultado.iteraciones[-1].c


def test_punto_medio_grande_no_desborda():
    """Evita el infinito de a+b cuando el punto medio sí es representable."""
    assert math.isfinite(punto_medio(1e308, 1.6e308))
    resultado = biseccion(entrada("x-1.3e308", (1e308, 1.6e308), 0))
    assert resultado.estado in {"EXITO", "PRECISION_NO_ALCANZADA"}
    assert math.isfinite(resultado.aproximacion)
    json.dumps(asdict(resultado), default=str, allow_nan=False)


def test_ancho_fuera_de_capacidad_no_publica_infinito():
    """Rechaza intervalos cuyo ancho no cabe en el contrato de punto flotante."""
    resultado = biseccion(entrada("x", (-1e308, 1e308)))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ANCHO_NO_REPRESENTABLE"
    json.dumps(asdict(resultado), default=str, allow_nan=False)


@pytest.mark.parametrize("expresion,codigo", [
    ("sin()", "EXPRESION_INVALIDA"), ("pi(1)", "EXPRESION_INVALIDA"),
    ("sin", "EXPRESION_INVALIDA"), ("(-1)**0.5", "DOMINIO_INVALIDO"),
    ("exp(-1000)", "SUBDESBORDAMIENTO"), ("1/(x-0.1234)", "SINGULARIDAD_DETECTADA"),
    ("(x-1)/(x-0.1234)", "SINGULARIDAD_DETECTADA"),
])
def test_fallos_del_motor_tienen_codigo_estable(expresion, codigo):
    """Los fallos no dependen del texto de excepciones generado por Python."""
    resultado = biseccion(entrada(expresion, (-1, 1)))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == codigo
    assert resultado.aproximacion is None
    json.dumps(asdict(resultado), default=str, allow_nan=False)


def test_cero_evaluado_no_se_anuncia_como_prueba_simbolica():
    """Mantiene el motivo compatible y añade el diagnóstico que distingue cero numérico."""
    resultado = biseccion(entrada("x", (0, 2)))
    assert resultado.codigo_diagnostico == "CERO_EVALUADO"
    assert "no certifica exactitud simbólica" in resultado.mensaje


@pytest.mark.parametrize("decimales", [0, 2, 4, 6])
def test_convergencia_geometrica_y_traza_final(decimales):
    """La aproximación y métricas pertenecen al intervalo que satisface el criterio estricto."""
    resultado = biseccion(entrada(decimales=decimales))
    inferior, superior = resultado.intervalo_final
    assert resultado.estado == "EXITO"
    assert superior - inferior < resultado.error_absoluto
    assert inferior <= math.sqrt(2) <= superior
    assert resultado.aproximacion == resultado.iteraciones[-1].c
    assert resultado.metricas["residuo_final"] == resultado.iteraciones[-1].residuo


def test_error_relativo_numero_sin_redondeo_y_casos_indefinidos():
    """La traza conserva porcentajes pequeños además del texto de compatibilidad."""
    resultado = biseccion(entrada())
    assert resultado.iteraciones[0].error_relativo_valor is None
    fila = resultado.iteraciones[-1]
    assert fila.error_relativo == "0.00%"
    assert 0 < fila.error_relativo_valor < 0.005
    assert error_relativo_numerico(0, 1) is None
    assert error_relativo_numerico(1e-300, 1e300) is None


def test_limite_devuelve_el_ultimo_punto_evaluado():
    """No genera una aproximación adicional sin fila al agotar las iteraciones."""
    resultado = biseccion(entrada(limite=2))
    assert resultado.motivo_parada == "limite_iteraciones"
    assert resultado.aproximacion == resultado.iteraciones[-1].c
    assert resultado.intervalo_final == (resultado.iteraciones[-1].extremo_izquierdo, resultado.iteraciones[-1].extremo_derecho)


def test_entrada_directa_invalida_se_rechaza_en_el_motor():
    """El constructor de datos no permite saltarse la validación del servicio público."""
    assert biseccion(entrada(limite=0)).codigo_diagnostico == "ENTRADA_INVALIDA"
    assert biseccion(entrada(decimales=True)).codigo_diagnostico == "ENTRADA_INVALIDA"
