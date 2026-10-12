"""Inversión exacta, singularidad, trazabilidad y contrato matricial."""
from fractions import Fraction
import pytest
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.inverse import MatrixInverseSolver

_CLAVES_ESPERADAS = {
    "status", "message", "determinant", "augmented_initial_latex", "inverse", "inverse_latex",
    "steps", "verification_step", "verification_reverse_step", "transpose_property_step",
}


@pytest.fixture
def resolutor():
    """Crea un resolutor de inversión para cada caso."""
    return MatrixInverseSolver()


def _identidad(dimension):
    return Matrix(dimension, dimension, [
        [Fraction(1) if i == j else Fraction(0) for j in range(dimension)]
        for i in range(dimension)
    ])


def test_inversa_de_una_celda(resolutor):
    """La matriz de una celda conserva recíproco y determinante."""
    matriz = Matrix(1, 1, [[4]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SUCCESS"
    assert resultado["inverse"].get(0, 0) == Fraction(1, 4)
    assert resultado["determinant"] == Fraction(4)


def test_inversa_dos_por_dos_exacta(resolutor):
    """Las cuatro celdas conservan sus fracciones exactas."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SUCCESS"
    inversa = resultado["inverse"]
    assert inversa.get(0, 0) == Fraction(4, 7)
    assert inversa.get(0, 1) == Fraction(-3, 7)
    assert inversa.get(1, 0) == Fraction(-3, 14)
    assert inversa.get(1, 1) == Fraction(2, 7)
    assert resultado["determinant"] == Fraction(14)


def test_inversa_tres_por_tres_con_pivote_inicial_nulo(resolutor):
    """El intercambio inicial conserva todas las celdas de la inversa."""
    matriz = Matrix(3, 3, [[0, 1, 2], [1, 0, 3], [4, -3, 8]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SUCCESS"
    inversa = resultado["inverse"]
    esperada = [
        [Fraction(-9, 2), Fraction(7), Fraction(-3, 2)],
        [Fraction(-2), Fraction(4), Fraction(-1)],
        [Fraction(3, 2), Fraction(-2), Fraction(1, 2)],
    ]
    for i in range(3):
        for j in range(3):
            assert inversa.get(i, j) == esperada[i][j], f"Fallo en ({i},{j})"
    assert resultado["determinant"] == Fraction(-2)


def test_inversa_identidad_es_identidad(resolutor):
    """La identidad conserva su inversa y determinante unitarios."""
    resultado = resolutor.solve(_identidad(3))
    assert resultado["status"] == "SUCCESS"
    assert resultado["inverse"] == _identidad(3)
    assert resultado["determinant"] == Fraction(1)


def test_inversa_filas_duplicadas_devuelve_singularidad(resolutor):
    """La singularidad carece de inversa y de verificaciones aplicables."""
    matriz = Matrix(2, 2, [[1, 2], [1, 2]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SINGULAR"
    assert resultado["inverse"] is None
    assert resultado["determinant"] == Fraction(0)
    assert resultado["verification_step"] is None
    assert resultado["verification_reverse_step"] is None
    assert resultado["transpose_property_step"] is None


def test_inversa_filas_dependientes_tres_por_tres_devuelve_singularidad(resolutor):
    """La dependencia lineal impide obtener inversa."""
    matriz = Matrix(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SINGULAR"
    assert resultado["inverse"] is None


def test_inversa_matriz_nula_devuelve_singularidad(resolutor):
    """La matriz nula se informa como singular."""
    matriz = Matrix(2, 2, [[0, 0], [0, 0]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SINGULAR"


def test_inversa_matriz_no_cuadrada_devuelve_error(resolutor):
    """La forma rectangular devuelve un error explicativo sin inversa."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "ERROR"
    assert resultado["inverse"] is None
    assert "cuadrada" in resultado["message"].lower()


def test_verificacion_producto_directo_presente_y_correcta(resolutor):
    """El producto de la matriz por la inversa confirma identidad."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.solve(matriz)
    assert resultado["verification_step"] is not None
    assert resultado["verification_step"]["coincide"] is True


def test_verificacion_producto_inverso_presente_y_correcta(resolutor):
    """El producto en orden inverso también confirma identidad."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.solve(matriz)
    assert resultado["verification_reverse_step"] is not None
    assert resultado["verification_reverse_step"]["coincide"] is True


def test_propiedad_inversa_de_transpuesta_presente_y_correcta(resolutor):
    """La verificación confirma la relación entre inversa y transposición."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.solve(matriz)
    assert resultado["transpose_property_step"] is not None
    assert resultado["transpose_property_step"]["coincide"] is True


def test_propiedad_inversa_de_transpuesta_tres_por_tres(resolutor):
    """La propiedad conserva su verificación en tres dimensiones."""
    matriz = Matrix(3, 3, [[0, 1, 2], [1, 0, 3], [4, -3, 8]])
    resultado = resolutor.solve(matriz)
    assert resultado["transpose_property_step"]["coincide"] is True


def test_pasos_inversa_incluyen_matriz_descripcion_y_detalle_latex(resolutor):
    """Cada paso conserva los datos necesarios para reproducirlo."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.solve(matriz)
    assert len(resultado["steps"]) > 0
    for paso in resultado["steps"]:
        assert "description" in paso
        assert "matrix" in paso
        assert "detail_latex" in paso
        assert paso["detail_latex"] is not None


def test_primer_paso_inversa_describe_bloque_identidad(resolutor):
    """El planteamiento distingue el bloque identidad de un vector independiente."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.solve(matriz)
    descripcion = resultado["steps"][0]["description"]
    assert "[A|I]" in descripcion
    assert "[A|b]" not in descripcion


def test_inversa_incluye_latex_aumentado_con_separador(resolutor):
    """La matriz aumentada inicial conserva entorno y separación de bloques."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.solve(matriz)
    latex = resultado["augmented_initial_latex"]
    assert latex is not None
    assert "array" in latex
    assert "|" in latex


def test_inversa_conserva_denominador_grande(resolutor):
    """La inversión recupera los enteros que corresponden a las fracciones diagonales."""
    matriz = Matrix(2, 2, [[Fraction(1, 1001), 0], [0, Fraction(1, 1001)]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SUCCESS"
    assert resultado["inverse"].get(0, 0) == Fraction(1001)
    assert resultado["inverse"].get(1, 1) == Fraction(1001)


def test_inversa_fracciones_exactas(resolutor):
    """Las fracciones de entrada conservan las cuatro celdas exactas de salida."""
    matriz = Matrix(2, 2, [[Fraction(1, 2), Fraction(1, 3)], [Fraction(1, 4), Fraction(1, 5)]])
    resultado = resolutor.solve(matriz)
    assert resultado["status"] == "SUCCESS"
    inversa = resultado["inverse"]
    assert inversa.get(0, 0) == Fraction(12)
    assert inversa.get(0, 1) == Fraction(-20)
    assert inversa.get(1, 0) == Fraction(-15)
    assert inversa.get(1, 1) == Fraction(30)


def test_contrato_inversa_exitosa_conserva_claves_exactas(resolutor):
    """La respuesta exitosa conserva exactamente el contrato completo."""
    resultado = resolutor.solve(Matrix(2, 2, [[4, 6], [3, 8]]))
    assert set(resultado.keys()) == _CLAVES_ESPERADAS


def test_contrato_inversa_erronea_conserva_claves_exactas(resolutor):
    """La respuesta de error conserva exactamente las mismas claves."""
    resultado = resolutor.solve(Matrix(2, 3, [[1, 2, 3], [4, 5, 6]]))
    assert set(resultado.keys()) == _CLAVES_ESPERADAS


def test_contrato_inversa_singular_conserva_claves_exactas(resolutor):
    """La singularidad conserva exactamente las claves del contrato."""
    resultado = resolutor.solve(Matrix(2, 2, [[1, 2], [1, 2]]))
    assert set(resultado.keys()) == _CLAVES_ESPERADAS


def test_inversa_exitosa_incluye_latex_matricial(resolutor):
    """La inversa exitosa incluye un entorno matricial LaTeX."""
    resultado = resolutor.solve(Matrix(2, 2, [[4, 6], [3, 8]]))
    assert resultado["inverse_latex"] is not None
    assert "bmatrix" in resultado["inverse_latex"]


def test_inversa_no_modifica_entrada(resolutor):
    """La resolución conserva intacta la matriz recibida."""
    matriz = Matrix(2, 2, [[4, 6], [3, 8]])
    original = matriz.clone()
    resolutor.solve(matriz)
    assert matriz == original
