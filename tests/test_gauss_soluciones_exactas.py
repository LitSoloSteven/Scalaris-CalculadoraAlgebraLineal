"""Soluciones racionales, representación textual y columnas libres de Gauss."""
from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.linear_systems.gauss_jordan import GaussJordanSolver
from src.backend.utils.formatters import format_fraction_str


def test_solucion_unica_entera():
    """Devuelve los tres coeficientes enteros exactos."""
    aumentada = Matrix(3, 4, [
        [2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3],
    ])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert resultado["solution_exact"] == [Fraction(2), Fraction(3), Fraction(-1)]


def test_solucion_unica_fraccionaria():
    """Conserva los coeficientes racionales sin aproximación."""
    aumentada = Matrix(2, 3, [[2, 1, 1], [1, 3, 2]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert resultado["solution_exact"] == [Fraction(1, 5), Fraction(3, 5)]


def test_solucion_con_denominador_grande():
    """Preserva denominadores superiores a mil."""
    aumentada = Matrix(1, 2, [[1001, 1]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "UNIQUE_SOLUTION"
    assert resultado["solution_exact"] == [Fraction(1, 1001)]


def test_gauss_jordan_coincide_con_gauss():
    """Ambos procedimientos producen los mismos coeficientes exactos."""
    aumentada = Matrix(3, 4, [
        [2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3],
    ])
    resultado_gauss = GaussSolver(aumentada).solve()
    resultado_jordan = GaussJordanSolver(aumentada).solve()
    assert resultado_gauss["solution_exact"] == resultado_jordan["solution_exact"]


def test_variable_libre_impide_solucion_unica():
    """Una variable libre deja disponible la representación paramétrica."""
    aumentada = Matrix(1, 3, [[1, 1, 2]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "INFINITE_SOLUTIONS"
    assert resultado["solution_exact"] is None
    assert resultado["solution"] is not None


def test_rango_deficiente_impide_solucion_unica():
    """Un sistema de tres variables dependientes no tiene solución única."""
    aumentada = Matrix(3, 4, [
        [1, 2, 3, 6], [2, 4, 6, 12], [1, 1, 1, 3],
    ])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "INFINITE_SOLUTIONS"
    assert resultado["solution_exact"] is None


def test_sistema_incompatible_carece_de_solucion_exacta():
    """La contradicción entre filas produce ausencia de solución."""
    aumentada = Matrix(2, 3, [[1, 1, 1], [2, 2, 5]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "NO_SOLUTION"
    assert resultado["solution_exact"] is None


def test_clave_solucion_exacta_presente_en_todos_los_estados():
    """La respuesta conserva la clave aunque su valor sea nulo."""
    casos = [
        Matrix(1, 2, [[1, 1]]), Matrix(1, 3, [[1, 1, 2]]),
        Matrix(2, 3, [[1, 1, 1], [2, 2, 5]]),
    ]
    for aumentada in casos:
        resultado = GaussSolver(aumentada).solve()
        assert "solution_exact" in resultado, f"Falta en estado={resultado['status']}"


def test_representacion_textual_fraccionaria():
    """Las fracciones conservan su representación textual reducida."""
    aumentada = Matrix(2, 3, [[2, 1, 1], [1, 3, 2]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["solution"] == ["1/5", "3/5"]


def test_coeficientes_exactos_coinciden_con_texto():
    """Cada coeficiente racional corresponde a su representación textual."""
    aumentada = Matrix(3, 4, [
        [2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3],
    ])
    resultado = GaussSolver(aumentada).solve()
    for fraccion, texto in zip(resultado["solution_exact"], resultado["solution"]):
        assert format_fraction_str(fraccion) == texto


def test_solucion_unica_carece_de_columnas_libres():
    """Todos los coeficientes quedan determinados por pivotes."""
    aumentada = Matrix(2, 3, [[1, 0, 5], [0, 1, 3]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["free_cols"] == []


def test_una_columna_libre_excluye_termino_independiente():
    """El término independiente no se cuenta como variable libre."""
    aumentada = Matrix(1, 3, [[1, 2, 3]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "INFINITE_SOLUTIONS"
    assert resultado["free_cols"] == [1]


def test_varias_columnas_libres():
    """Identifica ambas variables que carecen de pivote."""
    aumentada = Matrix(1, 4, [[1, 2, 3, 4]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "INFINITE_SOLUTIONS"
    assert resultado["free_cols"] == [1, 2]


def test_sistema_incompatible_carece_de_columnas_libres():
    """Una contradicción impide ofrecer parámetros de solución."""
    aumentada = Matrix(2, 3, [[1, 1, 1], [2, 2, 5]])
    resultado = GaussSolver(aumentada).solve()
    assert resultado["status"] == "NO_SOLUTION"
    assert resultado["free_cols"] == []


def test_clave_columnas_libres_presente_en_todos_los_estados():
    """La respuesta conserva la clave para cada clasificación del sistema."""
    casos = [
        Matrix(1, 2, [[1, 1]]), Matrix(1, 3, [[1, 1, 2]]),
        Matrix(2, 3, [[1, 1, 1], [2, 2, 5]]),
    ]
    for aumentada in casos:
        resultado = GaussSolver(aumentada).solve()
        assert "free_cols" in resultado
