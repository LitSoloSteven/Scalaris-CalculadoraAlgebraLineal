"""Pruebas del controlador de operaciones con matrices."""
import json
from fractions import Fraction
import pytest

from src.frontend.controladores.operaciones_matrices.controlador_operaciones_matrices import (
    ControladorOperacionesMatrices,
)
from src.backend.resolutores.operaciones_matrices.captura_matrices import obtener_diccionario_matrices


def _llamar(expresion: str, matrices: dict) -> dict:
    """Ejecuta el controlador con la expresión y diccionario de matrices."""
    return json.loads(
        ControladorOperacionesMatrices.procesar_expresion(expresion, json.dumps(matrices))
    )


def test_construir_matrices_preserva_denominador_grande():
    """Verifica que denominadores grandes preserven precisión exacta en la matriz."""
    matrices = obtener_diccionario_matrices({
        "A": {"filas": 1, "columnas": 1, "datos": [["1/1001"]]}
    })
    assert matrices["A"].datos[0][0] == Fraction(1, 1001)


def test_expresion_simple_exitosa():
    """Verifica expresion simple exitosa."""
    matrices = {"A": {"filas": 1, "columnas": 1, "datos": [["2"]]}}
    resultado = _llamar("A", matrices)
    assert resultado["estado"] == "EXITO"
    assert resultado["variable_final"] == "A"


def test_falta_columnas_reporta_contexto():
    """Verifica falta columnas reporta contexto."""
    matrices = {"A": {"filas": 2, "datos": [[1, 2], [3, 4]]}}
    resultado = _llamar("A", matrices)
    assert resultado["estado"] == "ERROR"
    assert "columnas" in resultado["mensaje"]
    assert "A" in resultado["mensaje"]


def test_falta_filas_reporta_contexto():
    """Verifica falta filas reporta contexto."""
    matrices = {"A": {"columnas": 2, "datos": [[1, 2]]}}
    resultado = _llamar("A", matrices)
    assert resultado["estado"] == "ERROR"
    assert "filas" in resultado["mensaje"]


def test_datos_no_son_lista():
    """Verifica datos no son lista."""
    matrices = {"A": {"filas": 1, "columnas": 1, "datos": "abc"}}
    resultado = _llamar("A", matrices)
    assert resultado["estado"] == "ERROR"
    assert "lista" in resultado["mensaje"].lower()


def test_discrepancia_cantidad_filas():
    """Verifica discrepancia cantidad filas."""
    matrices = {"A": {"filas": 3, "columnas": 1, "datos": [["1"], ["2"]]}}
    resultado = _llamar("A", matrices)
    assert resultado["estado"] == "ERROR"
    assert "filas" in resultado["mensaje"]


def test_discrepancia_longitud_fila():
    """Verifica discrepancia longitud fila."""
    matrices = {"A": {"filas": 2, "columnas": 2, "datos": [[1], [3, 4]]}}
    resultado = _llamar("A", matrices)
    assert resultado["estado"] == "ERROR"
    assert "fila" in resultado["mensaje"].lower()
    assert "columnas" in resultado["mensaje"].lower()


def test_celda_no_numerica_reporta_coordenadas():
    """Verifica celda no numerica reporta coordenadas."""
    matrices = {"A": {"filas": 1, "columnas": 2, "datos": [["1", "abc"]]}}
    resultado = _llamar("A", matrices)
    assert resultado["estado"] == "ERROR"
    assert "[1,2]" in resultado["mensaje"]


def test_diccionario_matrices_vacio():
    """Verifica diccionario matrices vacio."""
    resultado = _llamar("A", {})
    assert resultado["estado"] == "ERROR"
    assert "matriz" in resultado["mensaje"].lower()


def test_json_malformado_retorna_contexto():
    """Verifica json malformado retorna contexto."""
    resultado = json.loads(
        ControladorOperacionesMatrices.procesar_expresion("A", "{no es json}")
    )
    assert resultado["estado"] == "ERROR"
    assert "JSON malformado" in resultado["mensaje"]


def test_matriz_no_definida_en_expresion():
    """Verifica matriz no definida en expresion."""
    matrices = {"A": {"filas": 1, "columnas": 1, "datos": [["1"]]}}
    resultado = _llamar("B", matrices)
    assert resultado["estado"] == "ERROR"
    assert "B" in resultado["mensaje"]
