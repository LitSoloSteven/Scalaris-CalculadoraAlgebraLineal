"""Determinantes exactos, pivoteo y propiedades de operaciones matriciales."""
from fractions import Fraction
import pytest
from src.backend.exceptions import DimensionMismatchError
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver


@pytest.fixture
def resolutor():
    """Crea el resolutor matricial utilizado en cada propiedad."""
    return MatrixOpsSolver()


def test_determinante_de_una_celda(resolutor):
    """El determinante de una celda coincide con su valor."""
    matriz = Matrix(1, 1, [[5]])
    assert resolutor.determinant(matriz) == Fraction(5)


def test_determinante_dos_por_dos_producto_cruzado(resolutor):
    """El caso de dos por dos conserva el producto cruzado exacto."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    assert resolutor.determinant(matriz) == Fraction(14)


def test_determinante_dos_por_dos_negativo(resolutor):
    """Una matriz con determinante negativo conserva el signo."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    assert resolutor.determinant(matriz) == Fraction(-2)


def test_determinante_tres_por_tres_unitario(resolutor):
    """El cálculo tridimensional conserva el determinante unitario."""
    matriz = Matrix(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    assert resolutor.determinant(matriz) == Fraction(1)


def test_determinante_tres_por_tres_con_signos_mixtos(resolutor):
    """Los coeficientes de signos mixtos conservan el resultado exacto."""
    matriz = Matrix(3, 3, [[1, -4, 2], [-2, 8, -9], [-1, 7, 0]])
    assert resolutor.determinant(matriz) == Fraction(15)


def test_determinante_cuatro_por_cuatro_con_pivoteo(resolutor):
    """El pivote inicial nulo requiere intercambio y conserva el signo final."""
    matriz = Matrix(4, 4, [[0, 1, 1, 0], [1, 0, 1, 0], [1, 1, 0, 0], [0, 0, 0, 1]])
    assert resolutor.determinant(matriz) == Fraction(2)


def test_determinante_triangular_superior(resolutor):
    """La matriz triangular superior conserva el producto diagonal."""
    matriz = Matrix(3, 3, [[1, 2, 3], [0, 4, 5], [0, 0, 6]])
    assert resolutor.determinant(matriz) == Fraction(24)


def test_determinante_triangular_inferior(resolutor):
    """La matriz triangular inferior conserva el producto diagonal."""
    matriz = Matrix(3, 3, [[1, 0, 0], [2, 3, 0], [4, 5, 6]])
    assert resolutor.determinant(matriz) == Fraction(18)


def test_determinante_filas_dependientes_es_cero(resolutor):
    """La dependencia lineal de filas produce determinante nulo."""
    matriz = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
    assert resolutor.determinant(matriz) == Fraction(0)


def test_determinante_filas_duplicadas_es_cero(resolutor):
    """Dos filas iguales producen una matriz singular."""
    matriz = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [1, 2, 3]])
    assert resolutor.determinant(matriz) == Fraction(0)


def test_determinante_columna_nula_es_cero(resolutor):
    """La columna nula conserva el determinante cero."""
    matriz = Matrix(3, 3, [[1, 0, 3], [4, 0, 6], [7, 0, 9]])
    assert resolutor.determinant(matriz) == Fraction(0)


def test_determinante_identidad_es_uno(resolutor):
    """La identidad de cuatro por cuatro tiene determinante unitario."""
    matriz = Matrix(4, 4, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    assert resolutor.determinant(matriz) == Fraction(1)


def test_intercambio_de_filas_invierte_signo_del_determinante(resolutor):
    """Un intercambio de filas cambia únicamente el signo."""
    matriz = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    intercambiada = matriz.clone()
    intercambiada.swap_rows(0, 1)
    assert resolutor.determinant(intercambiada) == -resolutor.determinant(matriz)


def test_determinante_producto_es_producto_de_determinantes(resolutor):
    """El producto matricial conserva la propiedad multiplicativa."""
    matriz_a = Matrix(2, 2, [[6, 1], [3, 2]])
    matriz_b = Matrix(2, 2, [[4, 3], [1, 2]])
    determinante_a = resolutor.determinant(matriz_a)
    determinante_b = resolutor.determinant(matriz_b)
    producto = resolutor.multiply(matriz_a, matriz_b)["result_matrix"]
    assert resolutor.determinant(producto) == determinante_a * determinante_b


def test_determinante_transpuesta_coincide_con_original(resolutor):
    """La transposición conserva el determinante."""
    matriz = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    transpuesta = resolutor.transpose(matriz)
    assert resolutor.determinant(transpuesta) == resolutor.determinant(matriz)


def test_determinante_fracciones_exactas(resolutor):
    """Los productos de fracciones conservan el determinante racional exacto."""
    matriz = Matrix(2, 2, [[Fraction(1, 2), Fraction(1, 3)], [Fraction(1, 4), Fraction(1, 5)]])
    assert resolutor.determinant(matriz) == Fraction(1, 60)


def test_determinante_conserva_denominador_grande(resolutor):
    """El producto de denominadores grandes no se aproxima."""
    matriz = Matrix(2, 2, [[Fraction(1, 1001), 0], [0, Fraction(1, 1001)]])
    assert resolutor.determinant(matriz) == Fraction(1, 1001 * 1001)


def test_determinante_interpreta_cadenas_exactamente(resolutor):
    """Las celdas textuales se interpretan como racionales exactos."""
    matriz = Matrix(2, 2, [["1/3", "2"], ["3", "1/4"]])
    assert resolutor.determinant(matriz) == Fraction(-71, 12)


def test_determinante_rechaza_matriz_no_cuadrada(resolutor):
    """Una matriz rectangular conserva la excepción de dimensiones."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    with pytest.raises(DimensionMismatchError):
        resolutor.determinant(matriz)


def test_determinante_no_modifica_entrada(resolutor):
    """El cálculo deja intacta la matriz proporcionada."""
    matriz = Matrix(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    original = matriz.clone()
    resolutor.determinant(matriz)
    assert matriz == original
