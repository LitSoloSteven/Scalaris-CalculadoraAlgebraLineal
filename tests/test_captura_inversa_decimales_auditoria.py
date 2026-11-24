"""Regresiones de precisión y errores controlados en la entrada JSON de inversa."""
import json
from fractions import Fraction

import pytest

from src.frontend.controladores.algebra.operaciones_inversas import ControladorOperacionesInversas
from src.frontend.controladores.compartido.pasos.utilidades import (
    parsear_carga_json,
    parsear_carga_json_exacta,
)


@pytest.mark.parametrize("literal", [
    "0.12345678901234567890123456789",
    "9007199254740993.125",
    "-0.00000000000000000000000000007",
    "0." + "0" * 120 + "1",
])
def test_inversa_conserva_decimales_json_y_textuales(literal):
    """Ambas representaciones conservan el valor racional y su inversa exactos."""
    carga_numerica = '{"dimension":1,"datos":[[' + literal + ']]}'
    carga_textual = json.dumps({"dimension": 1, "datos": [[literal]]})
    for carga in (carga_numerica, carga_textual):
        resultado = ControladorOperacionesInversas.procesar_inversa(carga)
        assert resultado["estado"] == "EXITO"
        assert resultado["matriz_a"].datos == [[Fraction(literal)]]
        assert resultado["determinante"] == Fraction(literal)
        assert resultado["inversa"].datos == [[1 / Fraction(literal)]]


def test_json_decimal_no_convierte_matriz_invertible_en_singular():
    """La diferencia inferior a la precisión binaria sigue siendo un pivote no nulo."""
    carga = '{"dimension":2,"datos":[[1.00000000000000000001,1],[1,1]]}'
    resultado = ControladorOperacionesInversas.procesar_inversa(carga)
    escala = 10 ** 20
    assert resultado["estado"] == "EXITO"
    assert resultado["determinante"] == Fraction(1, escala)
    assert resultado["inversa"].datos == [[escala, -escala], [-escala, escala + 1]]
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])


def test_parser_exacto_es_aditivo_y_conserva_enteros():
    """La nueva ruta retiene el literal decimal; la ruta anterior mantiene sus tipos."""
    carga = '{"dimension":1,"datos":[[0.123456789012345678901]]}'
    exacto, error_exacto = parsear_carga_json_exacta(carga)
    heredado, error_heredado = parsear_carga_json(carga)
    assert error_exacto is error_heredado is None
    assert type(exacto["dimension"]) is int
    assert exacto["datos"] == [["0.123456789012345678901"]]
    assert type(heredado["datos"][0][0]) is float


@pytest.mark.parametrize("carga", [
    None, 123, "[", "[]", "[" * 2000 + "]" * 2000,
    '{"dimension":1,"datos":[[' + "9" * 5000 + ']]}',
])
def test_cargas_invalidas_o_excesivas_devuelven_error(carga):
    """Los fallos del decodificador no escapan del contrato de inversa."""
    resultado = ControladorOperacionesInversas.procesar_inversa(carga)
    assert resultado["estado"] == "ERROR"
    assert resultado["inversa"] is None
    assert resultado["pasos"] == []


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity", "1e-1000", "1e1000"])
def test_literales_no_admitidos_no_se_convierten_en_cero(literal):
    """No finitos y notación científica se rechazan con la coordenada de la celda."""
    resultado = ControladorOperacionesInversas.procesar_inversa(
        '{"dimension":1,"datos":[[' + literal + ']]}'
    )
    assert resultado["estado"] == "ERROR"
    assert resultado["celda_error"] == [0, 0]
    assert resultado["inversa"] is None
