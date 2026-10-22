"""Errores de dimensiones, acceso matricial y filas irregulares."""
import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.operaciones import ResolutorOperacionesMatrices
from src.backend.excepciones import ErrorDiscrepanciaDimension, ErrorDatosMatriz
from src.backend.utilidades.validadores import (
    validar_mismas_dimensiones, validar_dimensiones_multiplicacion,
)


def test_suma_rechaza_dimensiones_incompatibles():
    """La suma informa incompatibilidad entre matrices de distinto tamaño."""
    izquierda = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    derecha = Matriz(3, 2, [[1, 2], [3, 4], [5, 6]])
    resultado = ResolutorOperacionesMatrices().sumar(izquierda, derecha)
    assert resultado["estado"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["mensaje"]


def test_resta_rechaza_dimensiones_incompatibles():
    """La resta informa incompatibilidad entre matrices de distinto tamaño."""
    izquierda = Matriz(2, 2, [[1, 2], [3, 4]])
    derecha = Matriz(1, 2, [[1, 2]])
    resultado = ResolutorOperacionesMatrices().restar(izquierda, derecha)
    assert resultado["estado"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["mensaje"]


def test_producto_rechaza_dimensiones_incompatibles():
    """El producto rechaza columnas izquierdas distintas de filas derechas."""
    izquierda = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    derecha = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = ResolutorOperacionesMatrices().multiplicar(izquierda, derecha)
    assert resultado["estado"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["mensaje"]


def test_validacion_de_dimensiones_iguales_lanza_error():
    """El validador rechaza tamaños distintos con la excepción de dominio."""
    izquierda = Matriz(2, 2)
    derecha = Matriz(3, 3)
    with pytest.raises(ErrorDiscrepanciaDimension):
        validar_mismas_dimensiones(izquierda, derecha)


def test_validacion_de_dimensiones_producto_lanza_error():
    """El validador rechaza un producto con dimensiones incompatibles."""
    izquierda = Matriz(2, 3)
    derecha = Matriz(2, 3)
    with pytest.raises(ErrorDiscrepanciaDimension):
        validar_dimensiones_multiplicacion(izquierda, derecha)


def test_acceso_rechaza_indice_negativo():
    """El acceso a una fila negativa lanza un error de índice."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        matriz.obtener(-1, 0)


def test_acceso_rechaza_fila_fuera_de_rango():
    """El acceso posterior a la última fila lanza un error de índice."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        matriz.obtener(2, 0)


def test_acceso_rechaza_columna_fuera_de_rango():
    """El acceso posterior a la última columna lanza un error de índice."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        matriz.obtener(0, 2)


def test_construccion_rechaza_fila_irregular():
    """Una fila incompleta produce la excepción de datos matriciales."""
    with pytest.raises(ErrorDatosMatriz):
        Matriz(2, 2, [[1, 2], [3]])
