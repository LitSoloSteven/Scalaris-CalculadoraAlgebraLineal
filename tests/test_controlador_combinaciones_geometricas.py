"""Resultados geométricos de combinaciones lineales exactas."""
import json
from src.frontend.controladores.geometria.controlador_geometria import ControladorGeometria


def test_combinacion_cadena_unica():
    """Verifica combinacion cadena unica."""
    carga = json.dumps({
        "objetivo": {"datos": ["3", "3"], "orientacion": "columna"},
        "vectores": [
            {"datos": ["1", "0"], "orientacion": "columna"},
            {"datos": ["0", "1"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["estado_solucion"] == "UNICA"
    cadena = resultado["cadena"]
    assert cadena is not None
    ultimo = cadena[-1]
    b_exacto = resultado["objetivo"]["exacta"]
    assert ultimo["exacta"] == b_exacto


def test_combinacion_soluciones_infinitas():
    """Verifica combinacion soluciones infinitas."""
    carga = json.dumps({
        "objetivo": {"datos": ["0", "0"], "orientacion": "columna"},
        "vectores": [
            {"datos": ["1", "0"], "orientacion": "columna"},
            {"datos": ["2", "0"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(carga)
    assert resultado["estado"] == "EXITO"
    if resultado["estado_solucion"] == "INFINITA":
        assert resultado["cadena"] is None
        assert resultado["representacion"] == "no_unica"


def test_combinacion_sin_solucion():
    """Verifica combinacion sin solucion."""
    carga = json.dumps({
        "objetivo": {"datos": ["0", "1"], "orientacion": "columna"},
        "vectores": [
            {"datos": ["1", "0"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["estado_solucion"] == "SIN_SOLUCION"
    assert resultado["objetivo_fuera_del_espacio_generado"]
    assert resultado["cadena"] is None


def test_combinacion_dimension_cuatro_invalida():
    """Verifica combinacion dimension cuatro invalida."""
    carga = json.dumps({
        "objetivo": {"datos": ["1", "2", "3", "4"], "orientacion": "columna"},
        "vectores": [
            {"datos": ["1", "0", "0", "0"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(carga)
    assert resultado["estado"] == "ERROR"
    assert resultado.get("codigo") == "dimension_invalida"
