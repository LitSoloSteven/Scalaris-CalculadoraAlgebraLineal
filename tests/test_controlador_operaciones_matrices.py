"""Pruebas del controlador de operaciones con matrices."""
import json
from fractions import Fraction
import pytest

from src.frontend.controladores.operaciones_matrices.controlador_operaciones_matrices import (
    ControladorOperacionesMatrices,
)


def _llamar(expresion: str, matrices: dict) -> dict:
    """Ejecuta el controlador con la expresión y diccionario de matrices."""
    return json.loads(
        ControladorOperacionesMatrices.procesar_expresion(expresion, json.dumps(matrices))
    )


def test_construir_matrices_preserva_denominador_grande():
    """Verifica que denominadores grandes preserven precisión exacta en la matriz."""
    matrices = ControladorOperacionesMatrices._construir_matrices({
        "A": {"rows": 1, "cols": 1, "data": [["1/1001"]]}
    })
    assert matrices["A"].datos[0][0] == Fraction(1, 1001)


def test_expresion_simple_exitosa():
    matrices = {"A": {"rows": 1, "cols": 1, "data": [["2"]]}}
    resultado = _llamar("A", matrices)
    assert resultado["status"] == "SUCCESS"
    assert resultado["final_variable"] == "A"


def test_falta_columnas_reporta_contexto():
    matrices = {"A": {"rows": 2, "data": [[1, 2], [3, 4]]}}
    resultado = _llamar("A", matrices)
    assert resultado["status"] == "ERROR"
    assert "cols" in resultado["message"]
    assert "A" in resultado["message"]


def test_falta_filas_reporta_contexto():
    matrices = {"A": {"cols": 2, "data": [[1, 2]]}}
    resultado = _llamar("A", matrices)
    assert resultado["status"] == "ERROR"
    assert "rows" in resultado["message"]


def test_datos_no_son_lista():
    matrices = {"A": {"rows": 1, "cols": 1, "data": "abc"}}
    resultado = _llamar("A", matrices)
    assert resultado["status"] == "ERROR"
    assert "lista" in resultado["message"].lower()


def test_discrepancia_cantidad_filas():
    matrices = {"A": {"rows": 3, "cols": 1, "data": [["1"], ["2"]]}}
    resultado = _llamar("A", matrices)
    assert resultado["status"] == "ERROR"
    assert "filas" in resultado["message"]


def test_discrepancia_longitud_fila():
    matrices = {"A": {"rows": 2, "cols": 2, "data": [[1], [3, 4]]}}
    resultado = _llamar("A", matrices)
    assert resultado["status"] == "ERROR"
    assert "fila" in resultado["message"].lower()
    assert "columnas" in resultado["message"].lower()


def test_celda_no_numerica_reporta_coordenadas():
    matrices = {"A": {"rows": 1, "cols": 2, "data": [["1", "abc"]]}}
    resultado = _llamar("A", matrices)
    assert resultado["status"] == "ERROR"
    assert "[1,2]" in resultado["message"]


def test_diccionario_matrices_vacio():
    resultado = _llamar("A", {})
    assert resultado["status"] == "ERROR"
    assert "matriz" in resultado["message"].lower()


def test_json_malformado_retorna_contexto():
    resultado = json.loads(
        ControladorOperacionesMatrices.procesar_expresion("A", "{no es json}")
    )
    assert resultado["status"] == "ERROR"
    assert "JSON malformado" in resultado["message"]


def test_matriz_no_definida_en_expresion():
    matrices = {"A": {"rows": 1, "cols": 1, "data": [["1"]]}}
    resultado = _llamar("B", matrices)
    assert resultado["status"] == "ERROR"
    assert "B" in resultado["message"]
