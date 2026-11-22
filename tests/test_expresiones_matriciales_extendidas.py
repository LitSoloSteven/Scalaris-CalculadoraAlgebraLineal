"""Regresión de operadores tipográficos, resultados exactos y presupuestos matriciales."""
from fractions import Fraction
import json
from unittest.mock import Mock

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.expresiones import evaluador as modulo_evaluador
from src.frontend.controladores.algebra.operaciones_matrices.base.controlador_operaciones_matrices import (
    ControladorOperacionesMatrices,
)


@pytest.fixture
def matrices() -> dict[str, Matriz]:
    """Entrega matrices cuadradas, rectangulares y singulares de aritmética exacta."""
    return {
        "A": Matriz(2, 2, [[2, 1], [0, 2]]),
        "B": Matriz(1, 2, [[3, -1]]),
        "C": Matriz(2, 2, [[1, 2], [2, 4]]),
    }


@pytest.mark.parametrize("signo", ["÷", "⁄", "∕"])
def test_division_escalar_exacta(matrices, signo):
    """Los tres signos de división conservan fracciones y pasos por celda."""
    respuesta = modulo_evaluador.EvaluadorExpresionesMatriciales().evaluar(f"A{signo}−(1+2)", matrices)
    assert respuesta["estado"] == "EXITO"
    assert respuesta["matriz_resultado"].datos == [[Fraction(-2, 3), Fraction(-1, 3)], [0, Fraction(-2, 3)]]
    paso, = respuesta["pasos_segmento"]
    assert paso["tipo_operacion"] == "División escalar"
    assert r"\frac" in paso["matriz_simbolica_latex"]
    assert any(celda.get("detalle_latex") for celda in paso["pasos_celda_a_celda"])


@pytest.mark.parametrize(("literal", "valor"), tuple(zip(
    "¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞↉",
    "1/4 1/2 3/4 1/7 1/9 1/10 1/3 2/3 1/5 2/5 3/5 4/5 1/6 5/6 1/8 3/8 5/8 7/8 0/3".split(),
)))
def test_fraccion_tipografica_y_por_mil(matrices, literal, valor):
    """Cada literal tipográfico se interpreta antes del producto implícito y admite por mil."""
    respuesta = modulo_evaluador.EvaluadorExpresionesMatriciales().evaluar(f"{literal}‰B", matrices)
    escala = Fraction(valor) / 1000
    assert respuesta["estado"] == "EXITO"
    assert respuesta["matriz_resultado"].datos == [[3 * escala, -escala]]


@pytest.mark.parametrize(("exponente", "superindice"), tuple(enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹")))
def test_potencias_matriciales_enteras(matrices, exponente, superindice):
    """Comprueba el valor cerrado de la potencia de la matriz triangular del ejemplo."""
    respuesta = modulo_evaluador.EvaluadorExpresionesMatriciales().evaluar(f"A{superindice}", matrices)
    assert respuesta["estado"] == "EXITO"
    diagonal = 2 ** exponente
    superior = exponente * diagonal // 2
    assert respuesta["matriz_resultado"].datos == [[diagonal, superior], [0, diagonal]]
    assert respuesta["pasos_segmento"][0]["tipo_operacion"] == "Potencia matricial"


def test_distingue_nombre_con_indice_y_exponente_de_varios_digitos(matrices):
    """Conserva los nombres con números y lee el superíndice consecutivo como un solo exponente."""
    evaluador = modulo_evaluador.EvaluadorExpresionesMatriciales()
    matrices["A2"] = Matriz(1, 1, [[2]])
    respuesta = evaluador.evaluar("A2¹⁰", matrices)
    assert respuesta["estado"] == "EXITO"
    assert respuesta["matriz_resultado"].datos == [[1024]]


@pytest.mark.parametrize(("expresion", "esperado", "tipo", "simbolo"), [
    ("A⁻¹", [[Fraction(1, 2), Fraction(-1, 4)], [0, Fraction(1, 2)]], "Inversión", "^{-1}"),
    ("A⊕B", [[2, 1, 0, 0], [0, 2, 0, 0], [0, 0, 3, -1]], "Suma directa", r"\oplus"),
    ("B⊗A", [[6, 3, -2, -1], [0, 6, 0, -2]], "Producto de Kronecker", r"\otimes"),
])
def test_operaciones_con_segmento(matrices, expresion, esperado, tipo, simbolo):
    """Cada operador expone un segmento con fórmula LaTeX, operandos y resultado."""
    respuesta = modulo_evaluador.EvaluadorExpresionesMatriciales().evaluar(expresion, matrices)
    assert respuesta["estado"] == "EXITO"
    assert respuesta["matriz_resultado"].datos == esperado
    paso, = respuesta["pasos_segmento"]
    assert paso["tipo_operacion"] == tipo
    assert simbolo in paso["representacion_operacion"]
    assert simbolo in paso["matriz_simbolica_latex"]
    assert paso["matriz_resultado"].datos == esperado


@pytest.mark.parametrize(("expresion", "mensaje"), [
    ("A÷0", "cero"), ("A∕A", "divisor"), ("2⁄A", "divisor"),
    ("C⁻¹", "singular"), ("B⁰", "cuadrada"), ("2⊕A", "dos matrices"),
    ("A/2", "caracteres no soportados"),
    ("⊗A", "mal formada"), ("A÷", "mal formada"), ("(A⊕B", "desbalanceados"),
    ("A¹⁰⁰", "operaciones"), ("(999999999⁹)⁹⁹", "operaciones"),
    ("((999999999⁹)⁹)⁹A", "grandes"),
])
def test_errores_sin_traza_parcial(matrices, expresion, mensaje):
    """Devuelve errores específicos de sintaxis, dominio y tamaño con el contrato de error."""
    respuesta = modulo_evaluador.EvaluadorExpresionesMatriciales().evaluar(expresion, matrices)
    assert respuesta["estado"] == "ERROR"
    assert mensaje in respuesta["mensaje"]
    assert respuesta["pasos_segmento"] == []


def test_kronecker_compuesto_rechaza_el_bloque_antes_de_crearlo(monkeypatch):
    """Un 9×9 cabe en la traza, pero el siguiente bloque de 27×27 supera la reserva."""
    calcular = Mock(wraps=modulo_evaluador.producto_kronecker)
    monkeypatch.setitem(modulo_evaluador._BLOQUES, "⊗", (calcular, r"\otimes", "Producto de Kronecker"))
    evaluador = modulo_evaluador.EvaluadorExpresionesMatriciales()
    matrices = {"A": Matriz(3, 3)}
    respuesta = evaluador.evaluar("A⊗A⊗A", matrices)
    assert respuesta["estado"] == "ERROR"
    assert "dimensiones" in respuesta["mensaje"]
    calcular.assert_called_once()
    assert evaluador.evaluar("A⊗A", matrices)["estado"] == "EXITO"


def test_controlador_serializa_expresion_compuesta():
    """La ruta de uso normal conserva datos y pasos para la captura y el reproductor."""
    matrices = json.dumps({
        "A": {"filas": 1, "columnas": 1, "datos": [["2"]]},
        "B": {"filas": 1, "columnas": 1, "datos": [["3"]]},
    })
    respuesta = json.loads(ControladorOperacionesMatrices.procesar_expresion("A÷½⊕B²⊗A⁻¹", matrices))
    assert respuesta["estado"] == "EXITO"
    assert respuesta["matriz_resultado"]["datos"] == [["4", "0"], ["0", "9/2"]]
    assert [paso["tipo_operacion"] for paso in respuesta["pasos_segmento"]] == [
        "División escalar", "Potencia matricial", "Inversión", "Producto de Kronecker", "Suma directa",
    ]
