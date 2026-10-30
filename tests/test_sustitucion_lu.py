"""Comprueba sustituciones triangulares y datos acumulados exactos."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.sustitucion_lu import sustituir_adelante, sustituir_atras


def test_sustituciones_con_fracciones():
    inferior = Matriz(2, 2, [[1, 0], [Fraction(1, 2), 1]])
    superior = Matriz(2, 2, [[2, 1], [0, Fraction(5, 2)]])
    intermedio, filas_inferiores = sustituir_adelante(inferior, [Fraction(3), Fraction(5)])
    solucion, filas_superiores = sustituir_atras(superior, intermedio)
    assert intermedio == [Fraction(3), Fraction(7, 2)]
    assert solucion == [Fraction(4, 5), Fraction(7, 5)]
    assert filas_inferiores[1]["acumulado"] == Fraction(3, 2)
    assert [fila["fila"] for fila in filas_superiores] == [1, 0]
    assert filas_superiores[1]["productos"] == [Fraction(7, 5)]
