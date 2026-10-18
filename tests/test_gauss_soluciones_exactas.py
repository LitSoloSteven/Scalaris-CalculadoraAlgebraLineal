"""Soluciones racionales, representación textual y columnas libres de Gauss."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan
from src.backend.utilidades.formateadores import formatear_fraccion_texto


def test_solucion_unica_entera():
    """Devuelve los tres coeficientes enteros exactos."""
    aumentada = Matriz(3, 4, [
        [2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3],
    ])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion_exacta"] == [Fraction(2), Fraction(3), Fraction(-1)]


def test_solucion_unica_fraccionaria():
    """Conserva los coeficientes racionales sin aproximación."""
    aumentada = Matriz(2, 3, [[2, 1, 1], [1, 3, 2]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion_exacta"] == [Fraction(1, 5), Fraction(3, 5)]


def test_solucion_con_denominador_grande():
    """Preserva denominadores superiores a mil."""
    aumentada = Matriz(1, 2, [[1001, 1]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion_exacta"] == [Fraction(1, 1001)]


def test_gauss_jordan_coincide_con_gauss():
    """Ambos procedimientos producen los mismos coeficientes exactos."""
    aumentada = Matriz(3, 4, [
        [2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3],
    ])
    resultado_gauss = ResolutorGauss(aumentada).resolver()
    resultado_jordan = ResolutorGaussJordan(aumentada).resolver()
    assert resultado_gauss["solucion_exacta"] == resultado_jordan["solucion_exacta"]


def test_variable_libre_impide_solucion_unica():
    """Una variable libre deja disponible la representación paramétrica."""
    aumentada = Matriz(1, 3, [[1, 1, 2]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SOLUCIONES_INFINITAS"
    assert resultado["solucion_exacta"] is None
    assert resultado["solucion"] is not None


def test_rango_deficiente_impide_solucion_unica():
    """Un sistema de tres variables dependientes no tiene solución única."""
    aumentada = Matriz(3, 4, [
        [1, 2, 3, 6], [2, 4, 6, 12], [1, 1, 1, 3],
    ])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SOLUCIONES_INFINITAS"
    assert resultado["solucion_exacta"] is None


def test_sistema_incompatible_carece_de_solucion_exacta():
    """La contradicción entre filas produce ausencia de solución."""
    aumentada = Matriz(2, 3, [[1, 1, 1], [2, 2, 5]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SIN_SOLUCION"
    assert resultado["solucion_exacta"] is None


def test_clave_solucion_exacta_presente_en_todos_los_estados():
    """La respuesta conserva la clave aunque su valor sea nulo."""
    casos = [
        Matriz(1, 2, [[1, 1]]), Matriz(1, 3, [[1, 1, 2]]),
        Matriz(2, 3, [[1, 1, 1], [2, 2, 5]]),
    ]
    for aumentada in casos:
        resultado = ResolutorGauss(aumentada).resolver()
        assert "solucion_exacta" in resultado, f"Falta en estado={resultado['estado']}"


def test_representacion_textual_fraccionaria():
    """Las fracciones conservan su representación textual reducida."""
    aumentada = Matriz(2, 3, [[2, 1, 1], [1, 3, 2]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["solucion"] == ["1/5", "3/5"]


def test_coeficientes_exactos_coinciden_con_texto():
    """Cada coeficiente racional corresponde a su representación textual."""
    aumentada = Matriz(3, 4, [
        [2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3],
    ])
    resultado = ResolutorGauss(aumentada).resolver()
    for fraccion, texto in zip(resultado["solucion_exacta"], resultado["solucion"]):
        assert formatear_fraccion_texto(fraccion) == texto


def test_solucion_unica_carece_de_columnas_libres():
    """Todos los coeficientes quedan determinados por pivotes."""
    aumentada = Matriz(2, 3, [[1, 0, 5], [0, 1, 3]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["columnas_libres"] == []


def test_una_columna_libre_excluye_termino_independiente():
    """El término independiente no se cuenta como variable libre."""
    aumentada = Matriz(1, 3, [[1, 2, 3]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SOLUCIONES_INFINITAS"
    assert resultado["columnas_libres"] == [1]


def test_varias_columnas_libres():
    """Identifica ambas variables que carecen de pivote."""
    aumentada = Matriz(1, 4, [[1, 2, 3, 4]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SOLUCIONES_INFINITAS"
    assert resultado["columnas_libres"] == [1, 2]


def test_sistema_incompatible_carece_de_columnas_libres():
    """Una contradicción impide ofrecer parámetros de solución."""
    aumentada = Matriz(2, 3, [[1, 1, 1], [2, 2, 5]])
    resultado = ResolutorGauss(aumentada).resolver()
    assert resultado["estado"] == "SIN_SOLUCION"
    assert resultado["columnas_libres"] == []


def test_clave_columnas_libres_presente_en_todos_los_estados():
    """La respuesta conserva la clave para cada clasificación del sistema."""
    casos = [
        Matriz(1, 2, [[1, 1]]), Matriz(1, 3, [[1, 1, 2]]),
        Matriz(2, 3, [[1, 1, 1], [2, 2, 5]]),
    ]
    for aumentada in casos:
        resultado = ResolutorGauss(aumentada).resolver()
        assert "columnas_libres" in resultado
