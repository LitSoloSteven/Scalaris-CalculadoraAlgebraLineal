"""Pruebas de robustez y límites numéricos para controladores de geometría."""
import json
import pytest
from tests.comun_geometria import comprobar_error_longitud

from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
)


def test_rectas_planos_numero_excede_longitud_maxima():
    """Verifica rectas planos numero excede longitud maxima."""
    numero_enorme = "1" + "0" * 400
    carga = {
        "matriz_a": [
            [numero_enorme, "2"],
            ["1", "1"],
        ],
        "vector_b": ["1", "2"],
    }
    resultado = comprobar_error_longitud(carga, ControladorGeometria.procesar_rectas_planos)


def test_rectas_planos_vector_b_excede_longitud_maxima():
    """Verifica rectas planos vector b excede longitud maxima."""
    numero_enorme = "1" + "0" * 400
    carga = {
        "matriz_a": [
            ["1", "2"],
            ["1", "1"],
        ],
        "vector_b": [numero_enorme, "2"],
    }
    resultado = comprobar_error_longitud(carga, ControladorGeometria.procesar_rectas_planos)


def test_combinacion_vector_b_excesivo_sin_excepcion():
    """Verifica combinacion vector b excesivo sin excepcion."""
    numero_enorme = "1" + "0" * 400
    carga = {
        "objetivo": {"datos": [numero_enorme, "2"], "orientacion": "columna"},
        "vectores": [
            {"datos": ["1", "0"], "orientacion": "columna"},
            {"datos": ["0", "1"], "orientacion": "columna"},
        ],
    }
    resultado = comprobar_error_longitud(carga, ControladorGeometria.procesar_combinacion)


def test_combinacion_vector_columna_excesivo_sin_excepcion():
    """Verifica combinacion vector columna excesivo sin excepcion."""
    numero_enorme = "1" + "0" * 400
    carga = {
        "objetivo": {"datos": ["1", "2"], "orientacion": "columna"},
        "vectores": [
            {"datos": [numero_enorme, "0"], "orientacion": "columna"},
            {"datos": ["0", "1"], "orientacion": "columna"},
        ],
    }
    resultado = comprobar_error_longitud(carga, ControladorGeometria.procesar_combinacion)
