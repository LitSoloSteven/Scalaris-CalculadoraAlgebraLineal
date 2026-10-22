"""Determinantes exactos, pivoteo y propiedades de operaciones matriciales."""
from fractions import Fraction
import pytest
from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.operaciones import ResolutorOperacionesMatrices


@pytest.fixture
def resolutor():
    """Crea el resolutor matricial utilizado en cada propiedad."""
    return ResolutorOperacionesMatrices()


def test_determinante_de_una_celda(resolutor):
    """El determinante de una celda coincide con su valor."""
    matriz = Matriz(1, 1, [[5]])
    assert resolutor.determinante(matriz) == Fraction(5)


def test_determinante_dos_por_dos_producto_cruzado(resolutor):
    """El caso de dos por dos conserva el producto cruzado exacto."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    assert resolutor.determinante(matriz) == Fraction(14)


def test_determinante_dos_por_dos_negativo(resolutor):
    """Una matriz con determinante negativo conserva el signo."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    assert resolutor.determinante(matriz) == Fraction(-2)


def test_determinante_tres_por_tres_unitario(resolutor):
    """El cálculo tridimensional conserva el determinante unitario."""
    matriz = Matriz(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    assert resolutor.determinante(matriz) == Fraction(1)


def test_determinante_tres_por_tres_con_signos_mixtos(resolutor):
    """Los coeficientes de signos mixtos conservan el resultado exacto."""
    matriz = Matriz(3, 3, [[1, -4, 2], [-2, 8, -9], [-1, 7, 0]])
    assert resolutor.determinante(matriz) == Fraction(15)


def test_determinante_cuatro_por_cuatro_con_pivoteo(resolutor):
    """El pivote inicial nulo requiere intercambio y conserva el signo final."""
    matriz = Matriz(4, 4, [[0, 1, 1, 0], [1, 0, 1, 0], [1, 1, 0, 0], [0, 0, 0, 1]])
    assert resolutor.determinante(matriz) == Fraction(2)


def test_determinante_triangular_superior(resolutor):
    """La matriz triangular superior conserva el producto diagonal."""
    matriz = Matriz(3, 3, [[1, 2, 3], [0, 4, 5], [0, 0, 6]])
    assert resolutor.determinante(matriz) == Fraction(24)


def test_determinante_triangular_inferior(resolutor):
    """La matriz triangular inferior conserva el producto diagonal."""
    matriz = Matriz(3, 3, [[1, 0, 0], [2, 3, 0], [4, 5, 6]])
    assert resolutor.determinante(matriz) == Fraction(18)


def test_determinante_filas_dependientes_es_cero(resolutor):
    """La dependencia lineal de filas produce determinante nulo."""
    matriz = Matriz(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
    assert resolutor.determinante(matriz) == Fraction(0)


def test_determinante_filas_duplicadas_es_cero(resolutor):
    """Dos filas iguales producen una matriz singular."""
    matriz = Matriz(3, 3, [[1, 2, 3], [4, 5, 6], [1, 2, 3]])
    assert resolutor.determinante(matriz) == Fraction(0)


def test_determinante_columna_nula_es_cero(resolutor):
    """La columna nula conserva el determinante cero."""
    matriz = Matriz(3, 3, [[1, 0, 3], [4, 0, 6], [7, 0, 9]])
    assert resolutor.determinante(matriz) == Fraction(0)


def test_determinante_identidad_es_uno(resolutor):
    """La identidad de cuatro por cuatro tiene determinante unitario."""
    matriz = Matriz(4, 4, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    assert resolutor.determinante(matriz) == Fraction(1)


def test_intercambio_de_filas_invierte_signo_del_determinante(resolutor):
    """Un intercambio de filas cambia únicamente el signo."""
    matriz = Matriz(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    intercambiada = matriz.clonar()
    intercambiada.intercambiar_filas(0, 1)
    assert resolutor.determinante(intercambiada) == -resolutor.determinante(matriz)


def test_determinante_producto_es_producto_de_determinantes(resolutor):
    """El producto matricial conserva la propiedad multiplicativa."""
    matriz_a = Matriz(2, 2, [[6, 1], [3, 2]])
    matriz_b = Matriz(2, 2, [[4, 3], [1, 2]])
    determinante_a = resolutor.determinante(matriz_a)
    determinante_b = resolutor.determinante(matriz_b)
    producto = resolutor.multiplicar(matriz_a, matriz_b)["matriz_resultado"]
    assert resolutor.determinante(producto) == determinante_a * determinante_b


def test_determinante_transpuesta_coincide_con_original(resolutor):
    """La transposición conserva el determinante."""
    matriz = Matriz(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    transpuesta = resolutor.transponer(matriz)
    assert resolutor.determinante(transpuesta) == resolutor.determinante(matriz)


def test_determinante_fracciones_exactas(resolutor):
    """Los productos de fracciones conservan el determinante racional exacto."""
    matriz = Matriz(2, 2, [[Fraction(1, 2), Fraction(1, 3)], [Fraction(1, 4), Fraction(1, 5)]])
    assert resolutor.determinante(matriz) == Fraction(1, 60)


def test_determinante_conserva_denominador_grande(resolutor):
    """El producto de denominadores grandes no se aproxima."""
    matriz = Matriz(2, 2, [[Fraction(1, 1001), 0], [0, Fraction(1, 1001)]])
    assert resolutor.determinante(matriz) == Fraction(1, 1001 * 1001)


def test_determinante_interpreta_cadenas_exactamente(resolutor):
    """Las celdas textuales se interpretan como racionales exactos."""
    matriz = Matriz(2, 2, [["1/3", "2"], ["3", "1/4"]])
    assert resolutor.determinante(matriz) == Fraction(-71, 12)


def test_determinante_rechaza_matriz_no_cuadrada(resolutor):
    """Una matriz rectangular conserva la excepción de dimensiones."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    with pytest.raises(ErrorDiscrepanciaDimension):
        resolutor.determinante(matriz)


def test_determinante_no_modifica_entrada(resolutor):
    """El cálculo deja intacta la matriz proporcionada."""
    matriz = Matriz(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]])
    original = matriz.clonar()
    resolutor.determinante(matriz)
    assert matriz == original
