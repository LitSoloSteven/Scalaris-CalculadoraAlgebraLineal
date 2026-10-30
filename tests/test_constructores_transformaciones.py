"""Pruebas de los constructores de transformaciones notables."""
import pytest
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.aplicacion_transformacion import (
    matriz_rotacion,
    matriz_reflexion,
    matriz_escala,
    matriz_cizalladura,
)


@pytest.mark.parametrize("grados", [0, 90, 180, 270, -90, 360])
def test_rotacion_exacta(grados):
    """Verifica que los múltiplos de 90 generen matrices exactas."""
    matriz, es_exacta = matriz_rotacion(grados)
    assert es_exacta is True
    assert all(isinstance(valor, Fraction) for fila in matriz.datos for valor in fila)


def test_rotacion_aproximada():
    """Verifica que un ángulo no notable genere una matriz aproximada con flotantes."""
    matriz, es_exacta = matriz_rotacion(45)
    assert es_exacta is False
    assert any(isinstance(valor, float) for fila in matriz.datos for valor in fila)
    assert matriz.datos[0][0] == pytest.approx(0.707106, abs=1e-5)


def test_reflexion_x():
    """Verifica la reflexión sobre el eje x."""
    matriz = matriz_reflexion("x")
    assert matriz.datos == [[1, 0], [0, -1]]


def test_reflexion_origen():
    """Verifica la reflexión sobre el origen."""
    matriz = matriz_reflexion("origen")
    assert matriz.datos == [[-1, 0], [0, -1]]


def test_reflexion_invalida():
    """Verifica que un eje desconocido lance un error."""
    with pytest.raises(ValueError, match="Eje no válido"):
        matriz_reflexion("z")


def test_escala():
    """Verifica la matriz de escala con números enteros."""
    matriz = matriz_escala(2, 3)
    assert matriz.datos == [[2, 0], [0, 3]]


def test_cizalladura_x():
    """Verifica la cizalladura sobre el eje x."""
    matriz = matriz_cizalladura(2, "x")
    assert matriz.datos == [[1, 2], [0, 1]]


def test_cizalladura_eje_invalido():
    """Verifica que un eje desconocido lance un error."""
    with pytest.raises(ValueError, match="Eje de cizalladura"):
        matriz_cizalladura(2, "z")
        
@pytest.mark.parametrize("grados", [1, 17, 30, 45, 60, 89])
def test_rotacion_no_notable_es_aproximada(grados):
    """Verifica que ángulos no múltiplos de 90 devuelvan flotantes marcados como aproximados."""
    matriz, es_exacta = matriz_rotacion(grados)
    assert es_exacta is False
    assert any(isinstance(valor, float) for fila in matriz.datos for valor in fila)
    determinante = (
        matriz.datos[0][0] * matriz.datos[1][1]
        - matriz.datos[0][1] * matriz.datos[1][0]
    )
    assert determinante == pytest.approx(1.0, abs=1e-9)