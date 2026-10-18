"""Operaciones públicas de producto escalar y transposición matricial."""
from fractions import Fraction
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.operaciones import ResolutorOperacionesMatrices


def test_producto_escalar_matricial_simple():
    """El factor entero multiplica todas las celdas y conserva dimensiones."""
    matriz = Matriz(2, 2, [[2, -1], [3, 4]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(3, matriz)
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos == [[6, -3], [9, 12]]
    assert resultado["matriz_resultado"].filas == 2
    assert resultado["matriz_resultado"].columnas == 2


def test_producto_escalar_matricial_cero():
    """El factor cero devuelve una matriz nula de igual dimensión."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(0, matriz)
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos == [[0, 0, 0], [0, 0, 0]]


def test_producto_escalar_matricial_negativo():
    """El factor negativo invierte cada signo."""
    matriz = Matriz(2, 2, [[1, -2], [3, -4]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(-1, matriz)
    assert resultado["matriz_resultado"].datos == [[-1, 2], [-3, 4]]


def test_producto_escalar_matricial_conserva_dimensiones():
    """La matriz rectangular conserva filas y columnas."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(2, matriz)
    assert resultado["matriz_resultado"].filas == 2
    assert resultado["matriz_resultado"].columnas == 3


def test_producto_escalar_matricial_fraccionario():
    """El factor racional conserva resultados exactos por celda."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(Fraction(1, 2), matriz)
    assert resultado["matriz_resultado"].datos == [
        [Fraction(1, 2), Fraction(2, 2)], [Fraction(3, 2), Fraction(4, 2)],
    ]


def test_producto_escalar_matricial_interpreta_fraccion_textual():
    """Un factor textual racional se interpreta sin aproximarlo."""
    matriz = Matriz(2, 2, [[4, 8], [12, 16]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar("3/4", matriz)
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"].datos == [[3, 6], [9, 12]]


def test_producto_escalar_matricial_conserva_denominador_grande():
    """El producto compensa el denominador sin truncar las celdas."""
    matriz = Matriz(2, 1, [[Fraction(1, 1001)], [Fraction(1, 1001)]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(1001, matriz)
    assert resultado["matriz_resultado"].datos == [[1], [1]]


def test_producto_escalar_matricial_recupera_fraccion_de_flotante():
    """Un factor flotante simple devuelve celdas racionales exactas."""
    matriz = Matriz(1, 2, [[3, 5]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(0.5, matriz)
    assert resultado["matriz_resultado"].datos == [[Fraction(3, 2), Fraction(5, 2)]]


def test_producto_escalar_matricial_rechaza_cadena_invalida():
    """El factor no numérico devuelve estado y mensaje de error."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar("abc", matriz)
    assert resultado["estado"] == "ERROR"
    assert resultado["matriz_resultado"] is None
    assert "Escalar inválido" in resultado["mensaje"]


def test_producto_escalar_matricial_rechaza_cadena_vacia():
    """La ausencia de factor devuelve error."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar("", matriz)
    assert resultado["estado"] == "ERROR"


def test_producto_escalar_matricial_rechaza_division_por_cero():
    """La división por cero se comunica como error de factor."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar("1/0", matriz)
    assert resultado["estado"] == "ERROR"
    assert "cero" in resultado["mensaje"].lower() or "inválido" in resultado["mensaje"].lower()


def test_producto_escalar_matricial_registra_cada_celda():
    """Cada celda genera un paso además del estado inicial."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(2, matriz)
    assert len(resultado["pasos"]) == 1 + 2 * 3


def test_producto_escalar_matricial_detalla_cada_celda_latex():
    """El número de detalles coincide con el número de celdas."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(2, matriz)
    assert len(resultado["detalles_latex"]) == 2 * 3


def test_producto_escalar_matricial_pasos_incluyen_estado_acumulado():
    """Cada componente calculada incorpora una matriz de resultado."""
    matriz = Matriz(1, 2, [[1, 2]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(3, matriz)
    assert resultado["pasos"][0]["matriz"] is None
    assert resultado["pasos"][1]["matriz"] is not None
    assert resultado["pasos"][2]["matriz"] is not None


def test_producto_escalar_matricial_detalle_latex_muestra_fraccion():
    """El detalle identifica la celda y su fracción."""
    matriz = Matriz(1, 1, [[Fraction(1, 2)]])
    resolutor = ResolutorOperacionesMatrices()
    resultado = resolutor.multiplicar_escalar(Fraction(1, 3), matriz)
    detalle = resultado["detalles_latex"][0]
    assert "\\frac" in detalle
    assert "C_{1,1}" in detalle


def test_transpuesta_matriz_cuadrada():
    """La transposición intercambia filas y columnas de la matriz cuadrada."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    transpuesta = ResolutorOperacionesMatrices().transponer(matriz)
    assert transpuesta.filas == 2 and transpuesta.columnas == 2
    assert transpuesta.obtener(0, 0) == 1
    assert transpuesta.obtener(0, 1) == 3
    assert transpuesta.obtener(1, 0) == 2
    assert transpuesta.obtener(1, 1) == 4


def test_transpuesta_matriz_rectangular():
    """La transpuesta cambia una matriz de dos por tres a tres por dos."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    transpuesta = ResolutorOperacionesMatrices().transponer(matriz)
    assert transpuesta.filas == 3 and transpuesta.columnas == 2
    assert transpuesta.obtener(0, 0) == 1
    assert transpuesta.obtener(1, 0) == 2
    assert transpuesta.obtener(2, 0) == 3
    assert transpuesta.obtener(0, 1) == 4
    assert transpuesta.obtener(1, 1) == 5
    assert transpuesta.obtener(2, 1) == 6


def test_transpuesta_conserva_fracciones_exactas():
    """La transposición mantiene los denominadores de todas las celdas."""
    matriz = Matriz(2, 2, [[Fraction(1, 3), Fraction(2, 7)],
                         [Fraction(-5, 11), Fraction(1, 1001)]])
    transpuesta = ResolutorOperacionesMatrices().transponer(matriz)
    assert transpuesta.obtener(0, 0) == Fraction(1, 3)
    assert transpuesta.obtener(0, 1) == Fraction(-5, 11)
    assert transpuesta.obtener(1, 0) == Fraction(2, 7)
    assert transpuesta.obtener(1, 1) == Fraction(1, 1001)


def test_transpuesta_vector_fila_produce_columna():
    """La transpuesta del vector fila conserva sus componentes en columna."""
    vector_fila = Matriz(1, 3, [[1, 2, 3]])
    transpuesta = ResolutorOperacionesMatrices().transponer(vector_fila)
    assert transpuesta.filas == 3 and transpuesta.columnas == 1
    assert [transpuesta.obtener(i, 0) for i in range(3)] == [1, 2, 3]


def test_transpuesta_no_modifica_matriz_original():
    """La operación devuelve datos propios y conserva intacta la entrada."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    transpuesta = ResolutorOperacionesMatrices().transponer(matriz)
    assert matriz.obtener(0, 0) == 1 and matriz.obtener(0, 1) == 2
    assert matriz.obtener(1, 0) == 3 and matriz.obtener(1, 1) == 4
    assert transpuesta is not matriz
    assert transpuesta.datos is not matriz.datos
