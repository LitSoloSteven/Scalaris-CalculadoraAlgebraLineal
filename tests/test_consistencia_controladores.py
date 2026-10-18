"""Pruebas de consistencia de contratos y respuestas entre controladores."""
from tests.comun_entradas import copiar_entrada_prueba
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


def test_gauss_rechaza_carga_tipo_lista():
    """Verifica gauss rechaza carga tipo lista."""
    respuesta = json.loads(ControladorGauss.procesar_sistema("[1, 2, 3]"))
    assert respuesta["estado"] == "ERROR"
    assert "objeto JSON" in respuesta["mensaje"]


def test_gauss_jordan_rechaza_carga_tipo_lista():
    """Verifica gauss jordan rechaza carga tipo lista."""
    respuesta = json.loads(ControladorGaussJordan.procesar_sistema("[1, 2, 3]"))
    assert respuesta["estado"] == "ERROR"
    assert "objeto JSON" in respuesta["mensaje"]


def test_gauss_rechaza_carga_tipo_cadena():
    """Verifica gauss rechaza carga tipo cadena."""
    respuesta = json.loads(ControladorGauss.procesar_sistema('"hello"'))
    assert respuesta["estado"] == "ERROR"
    assert "objeto JSON" in respuesta["mensaje"]


def test_gauss_jordan_verificacion_en_solucion_unica():
    """Verifica gauss jordan verificacion en solucion unica."""
    carga = {"matriz_a": [["2", "1"], ["1", "-1"]], "vector_b": ["5", "1"], "variables": None}
    respuesta = _llamar_gauss_jordan(carga)
    assert respuesta["estado"] == "SOLUCION_UNICA"
    assert len(respuesta["pasos_verificacion_latex"]) > 0


def test_gauss_jordan_verificacion_ausente_sin_solucion():
    """Verifica gauss jordan verificacion ausente sin solucion."""
    carga = {"matriz_a": [["1", "1"], ["1", "1"]], "vector_b": ["1", "2"], "variables": None}
    respuesta = _llamar_gauss_jordan(carga)
    assert respuesta["estado"] == "SIN_SOLUCION"
    assert respuesta["pasos_verificacion_latex"] == []


def test_gauss_verificacion_utiliza_fracciones_exactas():
    """Verifica gauss verificacion utiliza fracciones exactas."""
    carga = copiar_entrada_prueba('sistema_fraccionario')
    respuesta = _llamar_gauss(carga)
    assert respuesta["estado"] == "SOLUCION_UNICA"
    unido = " ".join(respuesta["pasos_verificacion_latex"])
    assert r"\frac{9}{7}" in unido
    assert "1.2857" not in unido
    assert "Correcto" in unido or r"\text{Correcto}" in unido


def test_ambos_controladores_sistemas_retornan_estado_error_en_mayusculas():
    """Verifica ambos controladores sistemas retornan estado error en mayusculas."""
    carga = json.dumps({"matriz_a": [[1, 2]], "vector_b": [3, 4, 5]})
    respuesta_gauss = json.loads(ControladorGauss.procesar_sistema(carga))
    respuesta_gj = json.loads(ControladorGaussJordan.procesar_sistema(carga))
    assert respuesta_gauss["estado"] == "ERROR"
    assert respuesta_gj["estado"] == "ERROR"


def test_estado_error_es_consistente_en_todos_los_controladores():
    """Verifica estado error es consistente en todos los controladores."""
    json_malformado = '{"matriz_a": '

    assert json.loads(ControladorGauss.procesar_sistema(json_malformado))["estado"] == "ERROR"
    assert json.loads(ControladorGaussJordan.procesar_sistema(json_malformado))["estado"] == "ERROR"
    assert json.loads(ControladorOperacionesMatrices.procesar_expresion("A", json_malformado))["estado"] == "ERROR"
