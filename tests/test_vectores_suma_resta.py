"""Suma, resta, orientación y trazabilidad de vectores exactos."""
from fractions import Fraction
from src.backend.excepciones import ErrorVectorInvalido
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores
from tests.comun_vectores import comprobar_suma_columna


def test_suma_vectores_columna():
    """La suma conserva la orientación y las tres componentes."""
    v1 = Matriz(3, 1, [[1], [2], [3]])
    v2 = Matriz(3, 1, [[4], [5], [6]])
    resultado = comprobar_suma_columna(v1, v2)


def test_suma_vectores_fila():
    """La suma de filas devuelve una fila."""
    v1 = Matriz(1, 2, [[1, 2]])
    v2 = Matriz(1, 2, [[3, 4]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos == [[4, 6]]
    assert resultado["matriz_resultado"].filas == 1
    assert resultado["matriz_resultado"].columnas == 2


def test_suma_fracciones_exactas():
    """Las fracciones complementarias producen enteros exactos."""
    v1 = Matriz(2, 1, [[Fraction(1, 2)], [Fraction(1, 3)]])
    v2 = Matriz(2, 1, [[Fraction(1, 2)], [Fraction(2, 3)]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["matriz_resultado"].datos == [[1], [1]]


def test_suma_conserva_denominador_grande():
    """Los denominadores mayores que mil no se truncan."""
    v1 = Matriz(2, 1, [[Fraction(1, 1001)], [0]])
    v2 = Matriz(2, 1, [[Fraction(1000, 1001)], [0]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["matriz_resultado"].datos == [[1], [0]]


def test_adicion_componentes_negativos():
    """La suma respeta los signos de cada componente."""
    v1 = Matriz(2, 1, [[-3], [5]])
    v2 = Matriz(2, 1, [[2], [-8]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["matriz_resultado"].datos == [[-1], [-3]]


def test_suma_columna_fila_transpone_en_modo_permisivo():
    """La segunda fila se adapta a la columna inicial."""
    v1 = Matriz(3, 1, [[1], [2], [3]])
    v2 = Matriz(1, 3, [[4, 5, 6]])
    resultado = comprobar_suma_columna(v1, v2)


def test_suma_fila_columna_transpone_en_modo_permisivo():
    """La orientación del primer vector determina el resultado."""
    v1 = Matriz(1, 3, [[4, 5, 6]])
    v2 = Matriz(3, 1, [[1], [2], [3]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["matriz_resultado"].datos == [[5, 7, 9]]
    assert resultado["matriz_resultado"].filas == 1
    assert resultado["matriz_resultado"].columnas == 3


def test_suma_registra_transposicion_aplicada():
    """El ajuste de orientación aparece en los pasos."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(1, 2, [[3, 4]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    descripciones = [paso["descripcion"] for paso in resultado["pasos"]]
    assert any("Ajuste de orientación" in descripcion for descripcion in descripciones)


def test_suma_estricta_rechaza_orientacion_distinta():
    """El modo estricto rechaza fila y columna aunque tengan igual dimensión."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(1, 2, [[3, 4]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2, estricto=True)
    assert resultado["estado"] == "ERROR"
    assert "estricto=True" in resultado["mensaje"]
    assert resultado["matriz_resultado"] is None


def test_suma_rechaza_matriz_no_vectorial():
    """Una matriz rectangular no se interpreta como vector."""
    v1 = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    v2 = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["estado"] == "ERROR"
    assert "se esperaba un vector" in resultado["mensaje"]
    assert "2×3" in resultado["mensaje"]


def test_suma_rechaza_dimensiones_distintas():
    """El mensaje identifica las dos dimensiones incompatibles."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(3, 1, [[1], [2], [3]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["estado"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["mensaje"]
    assert "dim 2" in resultado["mensaje"]
    assert "dim 3" in resultado["mensaje"]


def test_error_vectorial_pertenece_a_jerarquia_algebraica():
    """La excepción vectorial conserva su clase base de dominio."""
    from src.backend.excepciones import AlgebraLinealError
    assert issubclass(ErrorVectorInvalido, AlgebraLinealError)


def test_resta_vectores_columna():
    """La resta conserva las componentes en columna."""
    v1 = Matriz(3, 1, [[5], [7], [9]])
    v2 = Matriz(3, 1, [[1], [2], [3]])
    resultado = ResolutorOperacionesVectores().restar(v1, v2)
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos == [[4], [5], [6]]


def test_resta_fracciones_exactas():
    """La resta mantiene la precisión racional."""
    v1 = Matriz(2, 1, [[1], [1]])
    v2 = Matriz(2, 1, [[Fraction(1, 3)], [Fraction(1, 7)]])
    resultado = ResolutorOperacionesVectores().restar(v1, v2)
    assert resultado["matriz_resultado"].datos == [[Fraction(2, 3)], [Fraction(6, 7)]]


def test_resta_estricta_rechaza_fila_columna():
    """La resta estricta exige la misma orientación."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(1, 2, [[3, 4]])
    resultado = ResolutorOperacionesVectores().restar(v1, v2, estricto=True)
    assert resultado["estado"] == "ERROR"


def test_suma_registra_paso_inicial_y_cada_componente():
    """Tres componentes producen cuatro pasos incluyendo el inicial."""
    v1 = Matriz(3, 1, [[1], [2], [3]])
    v2 = Matriz(3, 1, [[4], [5], [6]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert len(resultado["pasos"]) == 4


def test_adicion_conteo_detalles_latex_coincide_con_componentes():
    """Los detalles contienen cada componente y el vector completo."""
    v1 = Matriz(3, 1, [[1], [2], [3]])
    v2 = Matriz(3, 1, [[4], [5], [6]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert len(resultado["detalles_latex"]) == 4
    for detalle in resultado["detalles_latex"][:3]:
        assert "w_{" in detalle
    assert resultado["detalles_latex"][-1] == resultado["vector_resultado_latex"]


def test_suma_pasos_acumulan_matriz_resultante():
    """Cada paso refleja las componentes calculadas hasta ese momento."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(2, 1, [[3], [4]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2)
    assert resultado["pasos"][0]["matriz"] is None
    assert resultado["pasos"][1]["matriz"].datos == [[4], [0]]
    assert resultado["pasos"][2]["matriz"].datos == [[4], [6]]


def test_suma_admite_nombres_personalizados():
    """Los nombres personalizados mantienen la operación exitosa."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(2, 1, [[3], [4]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2, nombre1="u", nombre2="v")
    assert resultado["estado"] == "EXITO"


def test_error_vectorial_utiliza_nombre_personalizado():
    """El mensaje conserva el nombre aportado por el consumidor."""
    v1 = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    v2 = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = ResolutorOperacionesVectores().sumar(v1, v2, nombre1="mi_vector")
    assert "mi_vector" in resultado["mensaje"]
