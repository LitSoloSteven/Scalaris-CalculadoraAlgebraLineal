"""Pruebas de consistencia de contratos y respuestas entre controladores."""
import json
import pytest

from src.frontend.controladores.sistemas_lineales.controlador_gauss import (
    ControladorGauss,
)
from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import (
    ControladorGaussJordan,
)
from src.frontend.controladores.operaciones_matrices.controlador_operaciones_matrices import (
    ControladorOperacionesMatrices,
)


def _llamar_gauss(carga: dict) -> dict:
    """Ejecuta el controlador de Gauss con un diccionario de carga."""
    return json.loads(ControladorGauss.procesar_sistema(json.dumps(carga)))


def _llamar_gauss_jordan(carga: dict) -> dict:
    """Ejecuta el controlador de Gauss-Jordan con un diccionario de carga."""
    return json.loads(ControladorGaussJordan.procesar_sistema(json.dumps(carga)))


def test_gauss_rechaza_payload_tipo_lista():
    respuesta = json.loads(ControladorGauss.procesar_sistema("[1, 2, 3]"))
    assert respuesta["status"] == "ERROR"
    assert "objeto JSON" in respuesta["message"]


def test_gauss_jordan_rechaza_payload_tipo_lista():
    respuesta = json.loads(ControladorGaussJordan.procesar_sistema("[1, 2, 3]"))
    assert respuesta["status"] == "ERROR"
    assert "objeto JSON" in respuesta["message"]


def test_gauss_rechaza_payload_tipo_cadena():
    respuesta = json.loads(ControladorGauss.procesar_sistema('"hello"'))
    assert respuesta["status"] == "ERROR"
    assert "objeto JSON" in respuesta["message"]


def test_gauss_jordan_verificacion_en_solucion_unica():
    carga = {"matrix_A": [["2", "1"], ["1", "-1"]], "vector_b": ["5", "1"], "variables": None}
    respuesta = _llamar_gauss_jordan(carga)
    assert respuesta["status"] == "UNIQUE_SOLUTION"
    assert len(respuesta["verification_steps_latex"]) > 0


def test_gauss_jordan_verificacion_ausente_sin_solucion():
    carga = {"matrix_A": [["1", "1"], ["1", "1"]], "vector_b": ["1", "2"], "variables": None}
    respuesta = _llamar_gauss_jordan(carga)
    assert respuesta["status"] == "NO_SOLUTION"
    assert respuesta["verification_steps_latex"] == []


def test_gauss_verificacion_utiliza_fracciones_exactas():
    carga = {
        "matrix_A": [["1", "2", "3"], ["3", "2", "1"], ["-1", "-2", "4"]],
        "vector_b": ["0", "2", "2"],
        "variables": None,
    }
    respuesta = _llamar_gauss(carga)
    assert respuesta["status"] == "UNIQUE_SOLUTION"
    unido = " ".join(respuesta["verification_steps_latex"])
    assert r"\frac{9}{7}" in unido
    assert "1.2857" not in unido
    assert "Correcto" in unido or r"\text{Correcto}" in unido


def test_ambos_controladores_sistemas_retornan_estado_error_en_mayusculas():
    carga = json.dumps({"matrix_A": [[1, 2]], "vector_b": [3, 4, 5]})
    respuesta_gauss = json.loads(ControladorGauss.procesar_sistema(carga))
    respuesta_gj = json.loads(ControladorGaussJordan.procesar_sistema(carga))
    assert respuesta_gauss["status"] == "ERROR"
    assert respuesta_gj["status"] == "ERROR"


def test_estado_error_es_consistente_en_todos_los_controladores():
    json_malformado = '{"matrix_A": '

    assert json.loads(ControladorGauss.procesar_sistema(json_malformado))["status"] == "ERROR"
    assert json.loads(ControladorGaussJordan.procesar_sistema(json_malformado))["status"] == "ERROR"
    assert json.loads(ControladorOperacionesMatrices.procesar_expresion("A", json_malformado))["status"] == "ERROR"
