"""Pruebas de robustez y límites numéricos para controladores de geometría."""
import json
import pytest

from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
)


def test_rectas_planos_numero_excede_longitud_maxima():
    numero_enorme = "1" + "0" * 400
    payload = {
        "matrix_A": [
            [numero_enorme, "2"],
            ["1", "1"],
        ],
        "vector_b": ["1", "2"],
    }
    resultado = ControladorGeometria.procesar_rectas_planos(json.dumps(payload))
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") is None
    assert "longitud máxima permitida" in resultado["message"]
    assert resultado["error_cell"] is not None


def test_rectas_planos_vector_b_excede_longitud_maxima():
    numero_enorme = "1" + "0" * 400
    payload = {
        "matrix_A": [
            ["1", "2"],
            ["1", "1"],
        ],
        "vector_b": [numero_enorme, "2"],
    }
    resultado = ControladorGeometria.procesar_rectas_planos(json.dumps(payload))
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") is None
    assert "longitud máxima permitida" in resultado["message"]
    assert resultado["error_cell"] is not None


def test_combinacion_vector_b_excesivo_sin_excepcion():
    numero_enorme = "1" + "0" * 400
    payload = {
        "b": {"data": [numero_enorme, "2"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    }
    resultado = ControladorGeometria.procesar_combinacion(json.dumps(payload))
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") is None
    assert "longitud máxima permitida" in resultado["message"]
    assert resultado["error_cell"] is not None


def test_combinacion_vector_columna_excesivo_sin_excepcion():
    numero_enorme = "1" + "0" * 400
    payload = {
        "b": {"data": ["1", "2"], "orientation": "column"},
        "vectors": [
            {"data": [numero_enorme, "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    }
    resultado = ControladorGeometria.procesar_combinacion(json.dumps(payload))
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") is None
    assert "longitud máxima permitida" in resultado["message"]
    assert resultado["error_cell"] is not None
