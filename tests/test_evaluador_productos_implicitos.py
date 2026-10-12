"""Sintaxis implícita y explícita de expresiones matriciales exactas."""
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator


def _evaluar(expresion, matrices):
    return MatrixExpressionEvaluator().evaluate(expresion, matrices)


def test_producto_implicito_de_dos_matrices():
    """Dos nombres contiguos representan el producto matricial."""
    matriz_a = Matrix(1, 1, [[2]])
    matriz_b = Matrix(1, 1, [[3]])
    resultado = _evaluar("AB", {"A": matriz_a, "B": matriz_b})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(6)


def test_producto_implicito_de_tres_matrices():
    """Tres nombres contiguos conservan el orden del producto."""
    matriz_a = Matrix(1, 1, [[2]])
    matriz_b = Matrix(1, 1, [[3]])
    matriz_c = Matrix(1, 1, [[4]])
    resultado = _evaluar("ABC", {"A": matriz_a, "B": matriz_b, "C": matriz_c})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(24)


def test_nombre_con_digito_se_interpreta_completo():
    """El dígito forma parte del nombre matricial."""
    matriz_a = Matrix(1, 1, [[5]])
    resultado = _evaluar("A2", {"A2": matriz_a})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(5)


def test_producto_implicito_con_escalar():
    """Un número delante del nombre multiplica la matriz."""
    matriz_a = Matrix(1, 1, [[5]])
    resultado = _evaluar("2A", {"A": matriz_a})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(10)


def test_nombre_con_guion_bajo_se_interpreta_completo():
    """El guion bajo se admite en el identificador matricial."""
    matriz_nombre_compuesto = Matrix(1, 1, [[7]])
    resultado = _evaluar("A_foo", {"A_foo": matriz_nombre_compuesto})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(7)


def test_producto_explicito_de_dos_matrices():
    """El asterisco conserva el producto matricial esperado."""
    matriz_a = Matrix(1, 1, [[2]])
    matriz_b = Matrix(1, 1, [[3]])
    resultado = _evaluar("A*B", {"A": matriz_a, "B": matriz_b})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(6)


def test_suma_de_nombres_simples():
    """La expresión suma las dos matrices registradas."""
    matriz_a = Matrix(1, 1, [[2]])
    matriz_b = Matrix(1, 1, [[3]])
    resultado = _evaluar("A + B", {"A": matriz_a, "B": matriz_b})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(5)


def test_suma_de_nombres_con_digitos():
    """Los nombres con dígitos conservan la operación de suma."""
    matriz_a = Matrix(2, 2, [[1, 0], [0, 1]])
    matriz_b = Matrix(2, 2, [[1, 2], [3, 4]])
    resultado = _evaluar("A3 + B3", {"A3": matriz_a, "B3": matriz_b})
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data[0][0] == Fraction(2)


def test_expresion_anidada_con_transpuesta():
    """Las variantes de transposición producen el mismo resultado exacto."""
    matriz_a = Matrix(2, 2, [[1, 2], [3, 4]])
    matriz_b = Matrix(2, 2, [[5, 6], [7, 8]])
    matriz_c = Matrix(2, 2, [[1, 0], [0, 1]])
    matriz_d = Matrix(2, 2, [[2, 1], [0, 3]])
    matrices = {"A": matriz_a, "B": matriz_b, "C": matriz_c, "D": matriz_d}
    for expresion in ("2A - B(C - Dᵀ)", "2A - B*(C - D^T)", "2A - B*(C - D^t)"):
        resultado = _evaluar(expresion, matrices)
        assert resultado["status"] == "SUCCESS"
        assert resultado["result_matrix"].data == [
            [Fraction(13), Fraction(16)], [Fraction(21), Fraction(24)],
        ]


def test_producto_escalar_admite_ambos_ordenes():
    """Las variantes explícitas e implícitas conservan el producto escalar."""
    matriz_a = Matrix(2, 2, [[1, 2], [3, 4]])
    matrices = {"A": matriz_a}
    primero = _evaluar("2 * A", matrices)
    segundo = _evaluar("A * 2", matrices)
    tercero = _evaluar("2A", matrices)
    cuarto = _evaluar("(A)2", matrices)
    esperado = [[Fraction(2), Fraction(4)], [Fraction(6), Fraction(8)]]
    for resultado in (primero, segundo, tercero, cuarto):
        assert resultado["status"] == "SUCCESS"
        assert resultado["result_matrix"].data == esperado


def test_transposicion_de_matriz_y_suma():
    """La transposición conserva las celdas de la matriz y de su suma."""
    matriz_a = Matrix(2, 2, [[1, 2], [3, 4]])
    matriz_b = Matrix(2, 2, [[5, 6], [7, 8]])
    matrices = {"A": matriz_a, "B": matriz_b}
    transpuesta = _evaluar("Aᵀ", matrices)
    assert transpuesta["status"] == "SUCCESS"
    assert transpuesta["result_matrix"].data == [[Fraction(1), Fraction(3)], [Fraction(2), Fraction(4)]]
    suma_transpuesta = _evaluar("(A + B)ᵀ", matrices)
    assert suma_transpuesta["status"] == "SUCCESS"
    assert suma_transpuesta["result_matrix"].data == [[Fraction(6), Fraction(10)], [Fraction(8), Fraction(12)]]


def test_negacion_simple_doble_y_de_producto():
    """La negación conserva los signos en cada forma de la expresión."""
    matriz_a = Matrix(2, 2, [[1, 2], [3, 4]])
    matriz_b = Matrix(2, 2, [[5, 6], [7, 8]])
    matrices = {"A": matriz_a, "B": matriz_b}
    negacion = _evaluar("-A", matrices)
    assert negacion["status"] == "SUCCESS"
    assert negacion["result_matrix"].data == [[Fraction(-1), Fraction(-2)], [Fraction(-3), Fraction(-4)]]
    doble_negacion = _evaluar("--A", matrices)
    assert doble_negacion["status"] == "SUCCESS"
    assert doble_negacion["result_matrix"].data == [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
    producto_negativo = _evaluar("A * -B", matrices)
    assert producto_negativo["status"] == "SUCCESS"
    assert producto_negativo["result_matrix"].data == [[Fraction(-19), Fraction(-22)], [Fraction(-43), Fraction(-50)]]
