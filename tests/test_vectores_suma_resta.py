"""Suma, resta, orientación y trazabilidad de vectores exactos."""
from fractions import Fraction
from src.backend.exceptions import InvalidVectorError
from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.operations import VectorOpsSolver


def test_suma_vectores_columna():
    """La suma conserva la orientación y las tres componentes."""
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(3, 1, [[4], [5], [6]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[5], [7], [9]]
    assert resultado["result_matrix"].rows == 3
    assert resultado["result_matrix"].cols == 1


def test_suma_vectores_fila():
    """La suma de filas devuelve una fila."""
    v1 = Matrix(1, 2, [[1, 2]])
    v2 = Matrix(1, 2, [[3, 4]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[4, 6]]
    assert resultado["result_matrix"].rows == 1
    assert resultado["result_matrix"].cols == 2


def test_suma_fracciones_exactas():
    """Las fracciones complementarias producen enteros exactos."""
    v1 = Matrix(2, 1, [[Fraction(1, 2)], [Fraction(1, 3)]])
    v2 = Matrix(2, 1, [[Fraction(1, 2)], [Fraction(2, 3)]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["result_matrix"].data == [[1], [1]]


def test_suma_conserva_denominador_grande():
    """Los denominadores mayores que mil no se truncan."""
    v1 = Matrix(2, 1, [[Fraction(1, 1001)], [0]])
    v2 = Matrix(2, 1, [[Fraction(1000, 1001)], [0]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["result_matrix"].data == [[1], [0]]


def test_adicion_componentes_negativos():
    """La suma respeta los signos de cada componente."""
    v1 = Matrix(2, 1, [[-3], [5]])
    v2 = Matrix(2, 1, [[2], [-8]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["result_matrix"].data == [[-1], [-3]]


def test_suma_columna_fila_transpone_en_modo_permisivo():
    """La segunda fila se adapta a la columna inicial."""
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(1, 3, [[4, 5, 6]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[5], [7], [9]]
    assert resultado["result_matrix"].rows == 3
    assert resultado["result_matrix"].cols == 1


def test_suma_fila_columna_transpone_en_modo_permisivo():
    """La orientación del primer vector determina el resultado."""
    v1 = Matrix(1, 3, [[4, 5, 6]])
    v2 = Matrix(3, 1, [[1], [2], [3]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["result_matrix"].data == [[5, 7, 9]]
    assert resultado["result_matrix"].rows == 1
    assert resultado["result_matrix"].cols == 3


def test_suma_registra_transposicion_aplicada():
    """El ajuste de orientación aparece en los pasos."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(1, 2, [[3, 4]])
    resultado = VectorOpsSolver().add(v1, v2)
    descripciones = [paso["description"] for paso in resultado["steps"]]
    assert any("Ajuste de orientación" in descripcion for descripcion in descripciones)


def test_suma_estricta_rechaza_orientacion_distinta():
    """El modo estricto rechaza fila y columna aunque tengan igual dimensión."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(1, 2, [[3, 4]])
    resultado = VectorOpsSolver().add(v1, v2, strict=True)
    assert resultado["status"] == "ERROR"
    assert "strict=True" in resultado["message"]
    assert resultado["result_matrix"] is None


def test_suma_rechaza_matriz_no_vectorial():
    """Una matriz rectangular no se interpreta como vector."""
    v1 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    v2 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["status"] == "ERROR"
    assert "se esperaba un vector" in resultado["message"]
    assert "2×3" in resultado["message"]


def test_suma_rechaza_dimensiones_distintas():
    """El mensaje identifica las dos dimensiones incompatibles."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(3, 1, [[1], [2], [3]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["status"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["message"]
    assert "dim 2" in resultado["message"]
    assert "dim 3" in resultado["message"]


def test_error_vectorial_pertenece_a_jerarquia_algebraica():
    """La excepción vectorial conserva su clase base de dominio."""
    from src.backend.exceptions import AlgebraLinealError
    assert issubclass(InvalidVectorError, AlgebraLinealError)


def test_resta_vectores_columna():
    """La resta conserva las componentes en columna."""
    v1 = Matrix(3, 1, [[5], [7], [9]])
    v2 = Matrix(3, 1, [[1], [2], [3]])
    resultado = VectorOpsSolver().subtract(v1, v2)
    assert resultado["status"] == "SUCCESS"
    assert resultado["result_matrix"].data == [[4], [5], [6]]


def test_resta_fracciones_exactas():
    """La resta mantiene la precisión racional."""
    v1 = Matrix(2, 1, [[1], [1]])
    v2 = Matrix(2, 1, [[Fraction(1, 3)], [Fraction(1, 7)]])
    resultado = VectorOpsSolver().subtract(v1, v2)
    assert resultado["result_matrix"].data == [[Fraction(2, 3)], [Fraction(6, 7)]]


def test_resta_estricta_rechaza_fila_columna():
    """La resta estricta exige la misma orientación."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(1, 2, [[3, 4]])
    resultado = VectorOpsSolver().subtract(v1, v2, strict=True)
    assert resultado["status"] == "ERROR"


def test_suma_registra_paso_inicial_y_cada_componente():
    """Tres componentes producen cuatro pasos incluyendo el inicial."""
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(3, 1, [[4], [5], [6]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert len(resultado["steps"]) == 4


def test_adicion_conteo_detalles_latex_coincide_con_componentes():
    """Los detalles contienen cada componente y el vector completo."""
    v1 = Matrix(3, 1, [[1], [2], [3]])
    v2 = Matrix(3, 1, [[4], [5], [6]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert len(resultado["latex_details"]) == 4
    for detalle in resultado["latex_details"][:3]:
        assert "w_{" in detalle
    assert resultado["latex_details"][-1] == resultado["result_vector_latex"]


def test_suma_pasos_acumulan_matriz_resultante():
    """Cada paso refleja las componentes calculadas hasta ese momento."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(2, 1, [[3], [4]])
    resultado = VectorOpsSolver().add(v1, v2)
    assert resultado["steps"][0]["matrix"] is None
    assert resultado["steps"][1]["matrix"].data == [[4], [0]]
    assert resultado["steps"][2]["matrix"].data == [[4], [6]]


def test_suma_admite_nombres_personalizados():
    """Los nombres personalizados mantienen la operación exitosa."""
    v1 = Matrix(2, 1, [[1], [2]])
    v2 = Matrix(2, 1, [[3], [4]])
    resultado = VectorOpsSolver().add(v1, v2, name1="u", name2="v")
    assert resultado["status"] == "SUCCESS"


def test_error_vectorial_utiliza_nombre_personalizado():
    """El mensaje conserva el nombre aportado por el consumidor."""
    v1 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    v2 = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = VectorOpsSolver().add(v1, v2, name1="mi_vector")
    assert "mi_vector" in resultado["message"]
