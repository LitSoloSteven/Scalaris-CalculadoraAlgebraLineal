"""Pruebas del controlador del método de Gauss-Jordan para resolución de sistemas."""
import json
import pytest

from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import (
    ControladorGaussJordan,
)


def _procesar(carga: dict) -> dict:
    """Ejecuta el procesamiento del sistema y decodifica el resultado JSON."""
    return json.loads(ControladorGaussJordan.procesar_sistema(json.dumps(carga)))


def test_solucion_unica_tres_por_tres():
    carga = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert resultado["solution"] == ["2", "3", "-1"]
    for paso in resultado["verification_steps_latex"]:
        assert "Incorrecto" not in paso


def test_vector_b_incompleto_es_rechazado():
    carga = {
        "matrix_A": [["1", "0"], ["0", "1"], ["1", "1"]],
        "vector_b": ["5"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "ERROR"
    assert "1" in resultado["message"] and "3" in resultado["message"]


def test_matriz_irregular_es_rechazada():
    carga = {
        "matrix_A": [["1", "2"], ["3"]],
        "vector_b": ["5", "6"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "ERROR"
    assert "fila" in resultado["message"].lower()


def test_division_por_cero_en_celda_es_capturada():
    """Verifica que '1/0' sea detectado y no lance excepción no controlada."""
    carga = {
        "matrix_A": [["1/0", "1"], ["1", "1"]],
        "vector_b": ["1", "1"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "ERROR"
    assert "numérico" in resultado["message"].lower() or "cero" in resultado["message"].lower()


def test_payload_json_malformado():
    resultado = json.loads(ControladorGaussJordan.procesar_sistema("no es json"))
    assert resultado["status"] == "ERROR"
    assert "JSON" in resultado["message"] or "json" in resultado["message"]


def test_sistema_sin_solucion():
    carga = {
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["3", "5"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "NO_SOLUTION"


def test_verificacion_con_solucion_fraccionaria():
    """Verifica que el sistema con solución fraccionaria verifique sin error."""
    carga = {
        "matrix_A": [["1", "2", "3"], ["3", "2", "1"], ["-1", "-2", "22"]],
        "vector_b": ["0", "9", "2"],
        "variables": ["x1", "x2", "x3"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert any("/" in s for s in resultado["solution"]), f"Se esperaba fracción en {resultado['solution']}"
    assert len(resultado["verification_steps_latex"]) > 0
    for paso in resultado["verification_steps_latex"]:
        assert "Incorrecto" not in paso, f"Verificación falló: {paso}"
