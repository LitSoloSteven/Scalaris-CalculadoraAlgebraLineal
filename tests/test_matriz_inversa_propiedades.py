"""Inversión exacta, singularidad, trazabilidad y contrato matricial."""
from tests.comun_entradas import copiar_entrada_prueba
from fractions import Fraction
import pytest
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa

_CLAVES_ESPERADAS = {
    "estado", "mensaje", "determinante", "inversa", "pasos",
    "paso_verificacion", "paso_verificacion_inverso", "paso_propiedad_transpuesta",
    "estado", "mensaje", "determinante", "matriz_aumentada_inicial_latex", "inversa", "inversa_latex",
    "pasos", "paso_verificacion", "paso_verificacion_inverso", "paso_propiedad_transpuesta",
}


@pytest.fixture
def resolutor():
    """Crea un resolutor de inversión para cada caso."""
    return ResolutorInversa()


def _identidad(dimension):
    return Matriz(dimension, dimension, [
        [Fraction(1) if i == j else Fraction(0) for j in range(dimension)]
        for i in range(dimension)
    ])


def test_inversa_de_una_celda(resolutor):
    """La matriz de una celda conserva recíproco y determinante."""
    matriz = Matriz(1, 1, [[4]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "EXITO"
    assert resultado["inversa"].obtener(0, 0) == Fraction(1, 4)
    assert resultado["determinante"] == Fraction(4)


def test_inversa_dos_por_dos_exacta(resolutor):
    """Las cuatro celdas conservan sus fracciones exactas."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "EXITO"
    inversa = resultado["inversa"]
    assert inversa.obtener(0, 0) == Fraction(4, 7)
    assert inversa.obtener(0, 1) == Fraction(-3, 7)
    assert inversa.obtener(1, 0) == Fraction(-3, 14)
    assert inversa.obtener(1, 1) == Fraction(2, 7)
    assert resultado["determinante"] == Fraction(14)


def test_inversa_tres_por_tres_con_pivote_inicial_nulo(resolutor):
    """El intercambio inicial conserva todas las celdas de la inversa."""
    matriz = Matriz(3, 3, [[0, 1, 2], [1, 0, 3], [4, -3, 8]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "EXITO"
    inversa = resultado["inversa"]
    esperada = copiar_entrada_prueba('inversa_tres_por_tres')
    for i in range(3):
        for j in range(3):
            assert inversa.obtener(i, j) == esperada[i][j], f"Fallo en ({i},{j})"
    assert resultado["determinante"] == Fraction(-2)


def test_inversa_identidad_es_identidad(resolutor):
    """La identidad conserva su inversa y determinante unitarios."""
    resultado = resolutor.resolver(_identidad(3))
    assert resultado["estado"] == "EXITO"
    assert resultado["inversa"] == _identidad(3)
    assert resultado["determinante"] == Fraction(1)


def test_inversa_filas_duplicadas_devuelve_singularidad(resolutor):
    """La singularidad carece de inversa y de verificaciones aplicables."""
    matriz = Matriz(2, 2, [[1, 2], [1, 2]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "SINGULAR"
    assert resultado["inversa"] is None
    assert resultado["determinante"] == Fraction(0)
    assert resultado["paso_verificacion"] is None
    assert resultado["paso_verificacion_inverso"] is None
    assert resultado["paso_propiedad_transpuesta"] is None


def test_inversa_filas_dependientes_tres_por_tres_devuelve_singularidad(resolutor):
    """La dependencia lineal impide obtener inversa."""
    matriz = Matriz(3, 3, [[1, 2, 3], [2, 4, 6], [7, 8, 9]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "SINGULAR"
    assert resultado["inversa"] is None


def test_inversa_matriz_nula_devuelve_singularidad(resolutor):
    """La matriz nula se informa como singular."""
    matriz = Matriz(2, 2, [[0, 0], [0, 0]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "SINGULAR"


def test_inversa_matriz_no_cuadrada_devuelve_error(resolutor):
    """La forma rectangular devuelve un error explicativo sin inversa."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "ERROR"
    assert resultado["inversa"] is None
    assert "cuadrada" in resultado["mensaje"].lower()


def test_verificacion_producto_directo_presente_y_correcta(resolutor):
    """El producto de la matriz por la inversa confirma identidad."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.resolver(matriz)
    assert resultado["paso_verificacion"] is not None
    assert resultado["paso_verificacion"]["coincide"] is True


def test_verificacion_producto_inverso_presente_y_correcta(resolutor):
    """El producto en orden inverso también confirma identidad."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.resolver(matriz)
    assert resultado["paso_verificacion_inverso"] is not None
    assert resultado["paso_verificacion_inverso"]["coincide"] is True


def test_propiedad_inversa_de_transpuesta_presente_y_correcta(resolutor):
    """La verificación confirma la relación entre inversa y transposición."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.resolver(matriz)
    assert resultado["paso_propiedad_transpuesta"] is not None
    assert resultado["paso_propiedad_transpuesta"]["coincide"] is True


def test_propiedad_inversa_de_transpuesta_tres_por_tres(resolutor):
    """La propiedad conserva su verificación en tres dimensiones."""
    matriz = Matriz(3, 3, [[0, 1, 2], [1, 0, 3], [4, -3, 8]])
    resultado = resolutor.resolver(matriz)
    assert resultado["paso_propiedad_transpuesta"]["coincide"] is True


def test_pasos_inversa_incluyen_matriz_descripcion_y_detalle_latex(resolutor):
    """Cada paso conserva los datos necesarios para reproducirlo."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.resolver(matriz)
    assert len(resultado["pasos"]) > 0
    for paso in resultado["pasos"]:
        assert "descripcion" in paso
        assert "matriz" in paso
        assert "detalle_latex" in paso
        assert paso["detalle_latex"] is not None


def test_primer_paso_inversa_describe_bloque_identidad(resolutor):
    """El planteamiento distingue el bloque identidad de un vector independiente."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.resolver(matriz)
    descripcion = resultado["pasos"][0]["descripcion"]
    assert "[A|I]" in descripcion
    assert "[A|b]" not in descripcion


def test_inversa_incluye_latex_aumentado_con_separador(resolutor):
    """La matriz aumentada inicial conserva entorno y separación de bloques."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    resultado = resolutor.resolver(matriz)
    latex = resultado["matriz_aumentada_inicial_latex"]
    assert latex is not None
    assert "array" in latex
    assert "|" in latex


def test_inversa_conserva_denominador_grande(resolutor):
    """La inversión recupera los enteros que corresponden a las fracciones diagonales."""
    matriz = Matriz(2, 2, [[Fraction(1, 1001), 0], [0, Fraction(1, 1001)]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "EXITO"
    assert resultado["inversa"].obtener(0, 0) == Fraction(1001)
    assert resultado["inversa"].obtener(1, 1) == Fraction(1001)


def test_inversa_fracciones_exactas(resolutor):
    """Las fracciones de entrada conservan las cuatro celdas exactas de salida."""
    matriz = Matriz(2, 2, [[Fraction(1, 2), Fraction(1, 3)], [Fraction(1, 4), Fraction(1, 5)]])
    resultado = resolutor.resolver(matriz)
    assert resultado["estado"] == "EXITO"
    inversa = resultado["inversa"]
    assert inversa.obtener(0, 0) == Fraction(12)
    assert inversa.obtener(0, 1) == Fraction(-20)
    assert inversa.obtener(1, 0) == Fraction(-15)
    assert inversa.obtener(1, 1) == Fraction(30)


def test_contrato_inversa_exitosa_conserva_claves_exactas(resolutor):
    """La respuesta exitosa conserva exactamente el contrato completo."""
    resultado = resolutor.resolver(Matriz(2, 2, [[4, 6], [3, 8]]))
    assert set(resultado.keys()) == _CLAVES_ESPERADAS


def test_contrato_inversa_erronea_conserva_claves_exactas(resolutor):
    """La respuesta de error conserva exactamente las mismas claves."""
    resultado = resolutor.resolver(Matriz(2, 3, [[1, 2, 3], [4, 5, 6]]))
    assert set(resultado.keys()) == _CLAVES_ESPERADAS


def test_contrato_inversa_singular_conserva_claves_exactas(resolutor):
    """La singularidad conserva exactamente las claves del contrato."""
    resultado = resolutor.resolver(Matriz(2, 2, [[1, 2], [1, 2]]))
    assert set(resultado.keys()) == _CLAVES_ESPERADAS


def test_inversa_exitosa_incluye_latex_matricial(resolutor):
    """La inversa exitosa incluye un entorno matricial LaTeX."""
    resultado = resolutor.resolver(Matriz(2, 2, [[4, 6], [3, 8]]))
    assert resultado["inversa_latex"] is not None
    assert "bmatrix" in resultado["inversa_latex"]


def test_inversa_no_modifica_entrada(resolutor):
    """La resolución conserva intacta la matriz recibida."""
    matriz = Matriz(2, 2, [[4, 6], [3, 8]])
    original = matriz.clonar()
    resolutor.resolver(matriz)
    assert matriz == original
