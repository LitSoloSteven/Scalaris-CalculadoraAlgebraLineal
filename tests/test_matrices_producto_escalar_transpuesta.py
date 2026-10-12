"""Operaciones públicas de producto escalar y transposición matricial."""
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver


def test_producto_escalar_matricial_simple():
    """El factor entero multiplica todas las celdas y conserva dimensiones."""
    matriz = Matrix(2, 2, [[2, -1], [3, 4]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(3, matriz)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[6, -3], [9, 12]]
    assert resultado["result_matrix"].rows == 2
    assert resultado["result_matrix"].cols == 2


def test_producto_escalar_matricial_cero():
    """El factor cero devuelve una matriz nula de igual dimensión."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(0, matriz)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[0, 0, 0], [0, 0, 0]]


def test_producto_escalar_matricial_negativo():
    """El factor negativo invierte cada signo."""
    matriz = Matrix(2, 2, [[1, -2], [3, -4]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(-1, matriz)
    assert resultado["result_matrix"].data == [[-1, 2], [-3, 4]]


def test_producto_escalar_matricial_conserva_dimensiones():
    """La matriz rectangular conserva filas y columnas."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(2, matriz)
    assert resultado["result_matrix"].rows == 2
    assert resultado["result_matrix"].cols == 3


def test_producto_escalar_matricial_fraccionario():
    """El factor racional conserva resultados exactos por celda."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(Fraction(1, 2), matriz)
    assert resultado["result_matrix"].data == [
        [Fraction(1, 2), Fraction(2, 2)], [Fraction(3, 2), Fraction(4, 2)],
    ]


def test_producto_escalar_matricial_interpreta_fraccion_textual():
    """Un factor textual racional se interpreta sin aproximarlo."""
    matriz = Matrix(2, 2, [[4, 8], [12, 16]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply("3/4", matriz)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[3, 6], [9, 12]]


def test_producto_escalar_matricial_conserva_denominador_grande():
    """El producto compensa el denominador sin truncar las celdas."""
    matriz = Matrix(2, 1, [[Fraction(1, 1001)], [Fraction(1, 1001)]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(1001, matriz)
    assert resultado["result_matrix"].data == [[1], [1]]


def test_producto_escalar_matricial_recupera_fraccion_de_flotante():
    """Un factor flotante simple devuelve celdas racionales exactas."""
    matriz = Matrix(1, 2, [[3, 5]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(0.5, matriz)
    assert resultado["result_matrix"].data == [[Fraction(3, 2), Fraction(5, 2)]]


def test_producto_escalar_matricial_rechaza_cadena_invalida():
    """El factor no numérico devuelve estado y mensaje de error."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply("abc", matriz)
    assert resultado["status"] == "ERROR"
    assert resultado["result_matrix"] is None
    assert "Escalar inválido" in resultado["message"]


def test_producto_escalar_matricial_rechaza_cadena_vacia():
    """La ausencia de factor devuelve error."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply("", matriz)
    assert resultado["status"] == "ERROR"


def test_producto_escalar_matricial_rechaza_division_por_cero():
    """La división por cero se comunica como error de factor."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply("1/0", matriz)
    assert resultado["status"] == "ERROR"
    assert "cero" in resultado["message"].lower() or "inválido" in resultado["message"].lower()


def test_producto_escalar_matricial_registra_cada_celda():
    """Cada celda genera un paso además del estado inicial."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(2, matriz)
    assert len(resultado["steps"]) == 1 + 2 * 3


def test_producto_escalar_matricial_detalla_cada_celda_latex():
    """El número de detalles coincide con el número de celdas."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(2, matriz)
    assert len(resultado["latex_details"]) == 2 * 3


def test_producto_escalar_matricial_pasos_incluyen_estado_acumulado():
    """Cada componente calculada incorpora una matriz de resultado."""
    matriz = Matrix(1, 2, [[1, 2]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(3, matriz)
    assert resultado["steps"][0]["matrix"] is None
    assert resultado["steps"][1]["matrix"] is not None
    assert resultado["steps"][2]["matrix"] is not None


def test_producto_escalar_matricial_detalle_latex_muestra_fraccion():
    """El detalle identifica la celda y su fracción."""
    matriz = Matrix(1, 1, [[Fraction(1, 2)]])
    resolutor = MatrixOpsSolver()
    resultado = resolutor.scalar_multiply(Fraction(1, 3), matriz)
    detalle = resultado["latex_details"][0]
    assert "\\frac" in detalle
    assert "C_{1,1}" in detalle


def test_transpuesta_matriz_cuadrada():
    """La transposición intercambia filas y columnas de la matriz cuadrada."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    transpuesta = MatrixOpsSolver().transpose(matriz)
    assert transpuesta.rows == 2 and transpuesta.cols == 2
    assert transpuesta.get(0, 0) == 1
    assert transpuesta.get(0, 1) == 3
    assert transpuesta.get(1, 0) == 2
    assert transpuesta.get(1, 1) == 4


def test_transpuesta_matriz_rectangular():
    """La transpuesta cambia una matriz de dos por tres a tres por dos."""
    matriz = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    transpuesta = MatrixOpsSolver().transpose(matriz)
    assert transpuesta.rows == 3 and transpuesta.cols == 2
    assert transpuesta.get(0, 0) == 1
    assert transpuesta.get(1, 0) == 2
    assert transpuesta.get(2, 0) == 3
    assert transpuesta.get(0, 1) == 4
    assert transpuesta.get(1, 1) == 5
    assert transpuesta.get(2, 1) == 6


def test_transpuesta_conserva_fracciones_exactas():
    """La transposición mantiene los denominadores de todas las celdas."""
    matriz = Matrix(2, 2, [[Fraction(1, 3), Fraction(2, 7)],
                         [Fraction(-5, 11), Fraction(1, 1001)]])
    transpuesta = MatrixOpsSolver().transpose(matriz)
    assert transpuesta.get(0, 0) == Fraction(1, 3)
    assert transpuesta.get(0, 1) == Fraction(-5, 11)
    assert transpuesta.get(1, 0) == Fraction(2, 7)
    assert transpuesta.get(1, 1) == Fraction(1, 1001)


def test_transpuesta_vector_fila_produce_columna():
    """La transpuesta del vector fila conserva sus componentes en columna."""
    vector_fila = Matrix(1, 3, [[1, 2, 3]])
    transpuesta = MatrixOpsSolver().transpose(vector_fila)
    assert transpuesta.rows == 3 and transpuesta.cols == 1
    assert [transpuesta.get(i, 0) for i in range(3)] == [1, 2, 3]


def test_transpuesta_no_modifica_matriz_original():
    """La operación devuelve datos propios y conserva intacta la entrada."""
    matriz = Matrix(2, 2, [[1, 2], [3, 4]])
    transpuesta = MatrixOpsSolver().transpose(matriz)
    assert matriz.get(0, 0) == 1 and matriz.get(0, 1) == 2
    assert matriz.get(1, 0) == 3 and matriz.get(1, 1) == 4
    assert transpuesta is not matriz
    assert transpuesta.data is not matriz.data
