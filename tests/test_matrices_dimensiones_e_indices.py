"""Errores de dimensiones, acceso matricial y filas irregulares."""
import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver
from src.backend.exceptions import DimensionMismatchError, MatrixDataError
from src.backend.utils.validators import (
    validate_same_dimensions, validate_multiplication_dimensions,
)


def test_suma_rechaza_dimensiones_incompatibles():
    """La suma informa incompatibilidad entre matrices de distinto tamaño."""
    izquierda = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    derecha = Matrix(3, 2, [[1, 2], [3, 4], [5, 6]])
    resultado = MatrixOpsSolver().add(izquierda, derecha)
    assert resultado["status"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["message"]


def test_resta_rechaza_dimensiones_incompatibles():
    """La resta informa incompatibilidad entre matrices de distinto tamaño."""
    izquierda = Matrix(2, 2, [[1, 2], [3, 4]])
    derecha = Matrix(1, 2, [[1, 2]])
    resultado = MatrixOpsSolver().subtract(izquierda, derecha)
    assert resultado["status"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["message"]


def test_producto_rechaza_dimensiones_incompatibles():
    """El producto rechaza columnas izquierdas distintas de filas derechas."""
    izquierda = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    derecha = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = MatrixOpsSolver().multiply(izquierda, derecha)
    assert resultado["status"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["message"]


def test_validacion_de_dimensiones_iguales_lanza_error():
    """El validador rechaza tamaños distintos con la excepción de dominio."""
    izquierda = Matrix(2, 2)
    derecha = Matrix(3, 3)
    with pytest.raises(DimensionMismatchError):
        validate_same_dimensions(izquierda, derecha)


def test_validacion_de_dimensiones_producto_lanza_error():
    """El validador rechaza un producto con dimensiones incompatibles."""
    izquierda = Matrix(2, 3)
    derecha = Matrix(2, 3)
    with pytest.raises(DimensionMismatchError):
        validate_multiplication_dimensions(izquierda, derecha)


def test_acceso_rechaza_indice_negativo():
    """El acceso a una fila negativa lanza un error de índice."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        matriz.get(-1, 0)


def test_acceso_rechaza_fila_fuera_de_rango():
    """El acceso posterior a la última fila lanza un error de índice."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        matriz.get(2, 0)


def test_acceso_rechaza_columna_fuera_de_rango():
    """El acceso posterior a la última columna lanza un error de índice."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    with pytest.raises(IndexError):
        matriz.get(0, 2)


def test_construccion_rechaza_fila_irregular():
    """Una fila incompleta produce la excepción de datos matriciales."""
    with pytest.raises(MatrixDataError):
        Matrix(2, 2, [[1, 2], [3]])
