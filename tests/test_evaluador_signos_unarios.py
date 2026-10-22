"""Precedencia del signo negativo en expresiones matriciales."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.evaluador import EvaluadorExpresionesMatriciales


def test_menos_unario_despues_de_producto():
    """El signo de la segunda matriz se aplica antes del producto."""
    izquierda = Matriz(1, 1, [[2]])
    derecha = Matriz(1, 1, [[3]])
    evaluador = EvaluadorExpresionesMatriciales()
    resultado = evaluador.evaluar("A*-B", {"A": izquierda, "B": derecha})
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos[0][0] == Fraction(-6)


def test_doble_menos_unario():
    """Dos signos negativos consecutivos conservan el valor original."""
    matriz = Matriz(1, 1, [[5]])
    evaluador = EvaluadorExpresionesMatriciales()
    resultado = evaluador.evaluar("--A", {"A": matriz})
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos[0][0] == Fraction(5)


def test_menos_unario_al_inicio():
    """Un signo negativo inicial invierte el valor de la matriz."""
    matriz = Matriz(1, 1, [[7]])
    evaluador = EvaluadorExpresionesMatriciales()
    resultado = evaluador.evaluar("-A", {"A": matriz})
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos[0][0] == Fraction(-7)


def test_menos_unario_entre_parentesis():
    """Los paréntesis conservan el signo negativo de la matriz."""
    matriz = Matriz(1, 1, [[3]])
    evaluador = EvaluadorExpresionesMatriciales()
    resultado = evaluador.evaluar("(-A)", {"A": matriz})
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos[0][0] == Fraction(-3)
