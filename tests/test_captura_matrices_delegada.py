"""Separación de captura cruda, dominio exacto y banderas de resultado."""
import json
from fractions import Fraction
from unittest.mock import Mock

import pytest

from src.backend.constantes import DIMENSION_MAXIMA_MATRICES
from src.backend.resolutores.operaciones_matrices.captura_matrices import obtener_diccionario_matrices
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.componentes.captura_matrices import PanelCapturaMatrices
from src.frontend.controladores.operaciones_matrices import ControladorOperacionesMatrices
from src.frontend.vistas.operaciones_matrices.mixin_contexto_matrices import _estado_sugerencias


def test_componente_recoge_texto_sin_parseo(monkeypatch):
    """Recoger texto inválido no invoca el validador ni construye matrices de dominio."""
    monkeypatch.setattr(ValidadorMatriz, "parsear_numero_exacto", Mock(side_effect=AssertionError("Parseo en captura")))
    panel = PanelCapturaMatrices()
    panel.matrices = {"A": {"filas": 1, "columnas": 2, "entradas": [[Mock(value="1/3"), Mock(value="invalido")]]}}
    assert panel.obtener_datos_crudos() == {
        "A": {"filas": 1, "columnas": 2, "datos": [["1/3", "invalido"]]},
    }


def test_backend_construye_matriz_exacta_y_completa_vacios():
    """El dominio conserva denominadores grandes, negativos y ceros de celdas vacías."""
    datos = {"A": {"filas": 1, "columnas": 4, "datos": [["1/1001", "-2/3", None, " "]]}}
    matriz = obtener_diccionario_matrices(datos)["A"]
    assert matriz.datos == [[Fraction(1, 1001), Fraction(-2, 3), Fraction(0), Fraction(0)]]
    assert ControladorOperacionesMatrices.obtener_matrices_serializadas(datos)["A"]["datos"] == [["1/1001", "-2/3", "0", "0"]]


@pytest.mark.parametrize("datos,mensaje", [
    ({"filas": True, "columnas": 1, "datos": [["0"]]}, "'filas'"),
    ({"filas": 1, "columnas": False, "datos": [["0"]]}, "'columnas'"),
    ({"filas": 1, "columnas": 1, "datos": [None]}, "fila 1 no es una lista"),
    ({"filas": 1, "columnas": 1, "datos": [["1/0"]]}, "[1,1]"),
    ({"filas": 1, "columnas": 1, "datos": [["1" * 257]]}, "longitud máxima"),
])
def test_backend_rechaza_entradas_invalidas(datos, mensaje):
    """Los errores de estructura y celdas se reportan antes de evaluar la expresión."""
    with pytest.raises(ValueError, match=mensaje.replace("[", r"\[").replace("]", r"\]")):
        obtener_diccionario_matrices({"A": datos})


@pytest.mark.parametrize("expresion,producto", [("A*A", True), ("AA", True), ("2A", False), ("A+A", False)])
def test_controlador_calcula_bandera_producto(expresion, producto):
    """La bandera conserva la heurística de producto explícito e implícito vigente."""
    datos = {"A": {"filas": 1, "columnas": 1, "datos": [["1/3"]]}}
    resultado = json.loads(ControladorOperacionesMatrices.procesar_expresion(expresion, json.dumps(datos)))
    assert resultado["estado"] == "EXITO"
    assert resultado["contiene_producto"] is producto
    assert resultado["error_dimensiones"] is False


def test_controlador_calcula_bandera_error_dimensiones():
    """La incompatibilidad de formas se clasifica antes de entregar el resultado a la vista."""
    datos = {
        "A": {"filas": 1, "columnas": 1, "datos": [["1"]]},
        "B": {"filas": 1, "columnas": 2, "datos": [["1", "2"]]},
    }
    resultado = json.loads(ControladorOperacionesMatrices.procesar_expresion("A+B", json.dumps(datos)))
    assert resultado["estado"] == "ERROR"
    assert resultado["error_dimensiones"] is True
    assert resultado["contiene_producto"] is False


def test_vista_consume_bandera_sin_clasificar_mensaje():
    """Las palabras del mensaje no sustituyen la bandera del backend en sugerencias."""
    assert _estado_sugerencias({"estado": "ERROR", "mensaje": "dimensiones", "error_dimensiones": False}, set()) == "error"
    assert _estado_sugerencias({"estado": "ERROR", "mensaje": "otro", "error_dimensiones": True}, set()) == "error_dimensiones"


@pytest.mark.parametrize("filas,columnas,permitida", [
    (DIMENSION_MAXIMA_MATRICES, DIMENSION_MAXIMA_MATRICES, True),
    (DIMENSION_MAXIMA_MATRICES + 1, DIMENSION_MAXIMA_MATRICES + 1, False),
    (1, 2, False),
])
def test_transferencia_inversa_usa_limite_unico(filas, columnas, permitida):
    """La derivación conserva la frontera inclusiva y la exigencia de matriz cuadrada."""
    datos = {"filas": filas, "columnas": columnas, "datos": [["0"] * columnas for _ in range(filas)]}
    resultado = ControladorOperacionesMatrices.preparar_inversa("A", datos)
    assert ("datos" in resultado) is permitida
    assert ("mensaje" in resultado) is not permitida
