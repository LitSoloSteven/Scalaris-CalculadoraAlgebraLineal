"""Pruebas del controlador del método de Gauss para resolución de sistemas."""
import json
import pytest

from src.frontend.controladores.sistemas_lineales.controlador_gauss import (
    ControladorGauss,
)


def _procesar(carga: dict) -> dict:
    """Ejecuta el procesamiento del sistema y decodifica el resultado JSON."""
    return json.loads(ControladorGauss.procesar_sistema(json.dumps(carga)))


def test_solucion_unica_tres_por_tres():
    carga = {
        "matrix_A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "vector_b": ["8", "-11", "-3"],
        "variables": ["x1", "x2", "x3"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert resultado["solution"] == ["2", "3", "-1"]
    assert len(resultado["intermediate_steps_latex"]) > 0
    assert len(resultado["verification_steps_latex"]) > 0
    for paso in resultado["verification_steps_latex"]:
        assert "Incorrecto" not in paso, f"Verificación falló: {paso}"


def test_vector_b_incompleto_es_rechazado():
    """Verifica que un vector independiente incompleto retorne error explícito."""
    carga = {
        "matrix_A": [["1", "0"], ["0", "1"], ["1", "1"]],
        "vector_b": ["5"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "ERROR"
    assert "1" in resultado["message"] and "3" in resultado["message"]


def test_matriz_irregular_es_rechazada():
    """Verifica el rechazo de matrices con filas de longitud dispar."""
    carga = {
        "matrix_A": [["1", "2"], ["3"]],
        "vector_b": ["5", "6"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "ERROR"
    assert "fila" in resultado["message"].lower()


def test_sistema_sin_solucion():
    """Verifica el diagnóstico correcto de inconsistencia."""
    carga = {
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["3", "5"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "NO_SOLUTION"
    assert resultado["solution"] is None
    assert "inconsistente" in resultado["classification"].lower()


def test_celda_no_numerica_reporta_coordenadas():
    """Verifica reporte exacto de coordenadas para celdas no válidas."""
    carga = {
        "matrix_A": [["abc", "1"], ["1", "1"]],
        "vector_b": ["1", "1"],
        "variables": ["x1", "x2"],
    }
    resultado = _procesar(carga)
    assert resultado["status"] == "ERROR"
    assert "A[1,1]" in resultado["message"]


def test_payload_json_malformado():
    """Verifica manejo seguro ante cadenas JSON con sintaxis rota."""
    resultado = json.loads(ControladorGauss.procesar_sistema("esto no es json {{{"))
    assert resultado["status"] == "ERROR"
    assert "JSON" in resultado["message"] or "json" in resultado["message"]


def test_verificacion_con_solucion_fraccionaria():
    """Verifica que la comprobación mantenga fracciones analíticas exactas."""
    carga = {
        "matrix_A": [
            ["1", "2", "3"],
            ["3", "2", "1"],
            ["-1", "-2", "4"],
        ],
        "vector_b": ["0", "2", "2"],
        "variables": None,
    }
    resultado = _procesar(carga)

    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert resultado["solution"] == ["9/7", "-15/14", "2/7"]

    unido = " ".join(resultado["verification_steps_latex"])
    assert r"\frac{9}{7}" in unido
    assert r"\frac{15}{14}" in unido
    assert r"\frac{2}{7}" in unido
    assert "1.2857" not in unido
    assert "1.0714" not in unido
    assert "0.2857" not in unido


def test_verificacion_ausente_sin_solucion():
    """Verifica que no se generen pasos de comprobación si el sistema no tiene solución."""
    carga = {
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["1", "2"],
        "variables": None,
    }
    resultado = _procesar(carga)

    assert resultado["status"] == "NO_SOLUTION"
    assert resultado["verification_steps_latex"] == []
