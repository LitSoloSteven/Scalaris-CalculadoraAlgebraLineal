"""Normalización exacta de celdas del modelo matricial."""
from fractions import Fraction
import pytest
from src.backend.models.matrix import Matrix
from src.backend.exceptions import MatrixDataError


def test_matriz_fraccion_textual_con_denominador_grande():
    """La celda conserva el denominador mayor que mil."""
    matriz = Matrix(1, 1, [["1/1001"]])
    assert matriz.data[0][0] == Fraction(1, 1001)


def test_matriz_fraccion_textual_simple():
    """La fracción textual se interpreta sin aproximación."""
    matriz = Matrix(1, 1, [["2/3"]])
    assert matriz.data[0][0] == Fraction(2, 3)


def test_matriz_decimal_textual_exacto():
    """El decimal textual se convierte en una fracción exacta."""
    matriz = Matrix(1, 1, [["0.1"]])
    assert matriz.data[0][0] == Fraction(1, 10)


def test_matriz_flotante_recupera_fraccion():
    """Un flotante equivalente a una fracción simple se normaliza."""
    matriz = Matrix(1, 1, [[0.5]])
    assert matriz.data[0][0] == Fraction(1, 2)


def test_matriz_celda_invalida_lanza_error_de_datos():
    """El contenido no numérico conserva la excepción de dominio."""
    with pytest.raises(MatrixDataError):
        Matrix(1, 1, [["abc"]])


def test_matriz_celda_vacia_se_convierte_en_cero():
    """La celda vacía tiene el valor racional cero."""
    matriz = Matrix(1, 1, [[""]])
    assert matriz.data[0][0] == Fraction(0)
