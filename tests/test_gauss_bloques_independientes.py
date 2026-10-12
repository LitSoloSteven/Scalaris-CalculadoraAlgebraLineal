"""Reducción de bloques independientes y compatibilidad de sistemas con un vector."""
from fractions import Fraction
import pytest
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver


def _aumentar_con_identidad(valores, dimension):
    filas = []
    for i in range(dimension):
        fila = [Fraction(valor) for valor in valores[i]]
        for j in range(dimension):
            fila.append(Fraction(1) if i == j else Fraction(0))
        filas.append(fila)
    return Matrix(dimension, 2 * dimension, filas)


def test_bloque_independiente_predeterminado_es_una_columna():
    """El resolutor conserva un vector independiente como valor predeterminado."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    assert GaussSolver(matriz).num_rhs == 1


def test_numero_de_columnas_independientes_debe_ser_entero_positivo():
    """Los tamaños nulos, negativos y no enteros conservan el error de validación."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    with pytest.raises(ValueError, match="num_rhs"):
        GaussSolver(matriz, num_rhs=0)
    with pytest.raises(ValueError, match="num_rhs"):
        GaussSolver(matriz, num_rhs=-1)
    with pytest.raises(ValueError, match="num_rhs"):
        GaussSolver(matriz, num_rhs=1.5)


def test_resolucion_de_sistema_rechaza_varias_columnas_independientes():
    """La resolución con sustitución conserva su contrato de una columna independiente."""
    matriz = Matrix(2, 4, [[1, 2, 1, 0], [3, 4, 0, 1]])
    resolutor = GaussJordanSolver(matriz, num_rhs=2)
    with pytest.raises(ValueError, match="num_rhs"):
        resolutor.solve()


def test_reduccion_dos_por_dos_produce_identidad_e_inversa():
    """La reducción del bloque aumentado produce los dos bloques exactos."""
    matriz = _aumentar_con_identidad([[4, 6], [3, 8]], 2)
    resolutor = GaussJordanSolver(matriz, num_rhs=2)
    resultado = resolutor.solve_reduction()
    reducida = resultado["reduced_matrix"]
    assert resultado["rank"] == 2
    assert resultado["pivot_cols"] == [0, 1]
    for i in range(2):
        for j in range(2):
            esperado = Fraction(1) if i == j else Fraction(0)
            assert reducida.get(i, j) == esperado
    assert reducida.get(0, 2) == Fraction(4, 7)
    assert reducida.get(0, 3) == Fraction(-3, 7)
    assert reducida.get(1, 2) == Fraction(-3, 14)
    assert reducida.get(1, 3) == Fraction(2, 7)


def test_reduccion_tres_por_tres_conserva_inversa_exacta():
    """La reducción con pivote inicial nulo mantiene la inversa racional."""
    matriz = _aumentar_con_identidad([[0, 1, 2], [1, 0, 3], [4, -3, 8]], 3)
    resolutor = GaussJordanSolver(matriz, num_rhs=3)
    resultado = resolutor.solve_reduction()
    reducida = resultado["reduced_matrix"]
    assert resultado["rank"] == 3
    inversa_esperada = [
        [Fraction(-9, 2), Fraction(7), Fraction(-3, 2)],
        [Fraction(-2), Fraction(4), Fraction(-1)],
        [Fraction(3, 2), Fraction(-2), Fraction(1, 2)],
    ]
    for i in range(3):
        for j in range(3):
            assert reducida.get(i, 3 + j) == inversa_esperada[i][j]


def test_reduccion_singular_tiene_rango_deficiente():
    """La matriz dependiente conserva rango menor que su dimensión."""
    matriz = _aumentar_con_identidad([[1, 2], [2, 4]], 2)
    resolutor = GaussJordanSolver(matriz, num_rhs=2)
    resultado = resolutor.solve_reduction()
    assert resultado["rank"] < 2
    reducida = resultado["reduced_matrix"]
    assert reducida.get(0, 0) == Fraction(1)
    assert reducida.get(1, 0) == Fraction(0)
    assert reducida.get(1, 1) == Fraction(0)


def test_reduccion_devuelve_pasos_y_metadatos():
    """El contrato conserva matriz reducida, rango, pivotes y pasos."""
    matriz = _aumentar_con_identidad([[4, 6], [3, 8]], 2)
    resolutor = GaussJordanSolver(matriz, num_rhs=2)
    resultado = resolutor.solve_reduction()
    assert "steps" in resultado
    assert len(resultado["steps"]) > 0
    assert "inicial" in resultado["steps"][0]["description"].lower()
    assert "reduced_matrix" in resultado
    assert "rank" in resultado
    assert "pivot_cols" in resultado


def test_sistema_de_una_columna_independiente_conserva_solucion():
    """La resolución habitual conserva la solución exacta del sistema."""
    matriz = Matrix(3, 4, [[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]])
    resultado = GaussSolver(matriz).solve()
    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert resultado["solution_exact"] == [Fraction(2), Fraction(3), Fraction(-1)]


def test_reduccion_conserva_denominador_grande():
    """El bloque inverso conserva fracciones con denominador mayor que mil."""
    matriz = _aumentar_con_identidad([[1001, 0], [0, 1001]], 2)
    resolutor = GaussJordanSolver(matriz, num_rhs=2)
    resultado = resolutor.solve_reduction()
    reducida = resultado["reduced_matrix"]
    assert reducida.get(0, 2) == Fraction(1, 1001)
    assert reducida.get(1, 3) == Fraction(1, 1001)


def test_reduccion_no_modifica_matriz_original():
    """La reducción conserva intacta la matriz recibida."""
    matriz = _aumentar_con_identidad([[4, 6], [3, 8]], 2)
    original = matriz.clone()
    GaussJordanSolver(matriz, num_rhs=2).solve_reduction()
    assert matriz == original
