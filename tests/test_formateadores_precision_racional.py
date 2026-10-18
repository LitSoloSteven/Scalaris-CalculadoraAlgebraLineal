"""Formato exacto de números, soluciones y matrices LaTeX."""
from fractions import Fraction
from src.backend.utilidades.formateadores import formatear_fraccion_texto, numero_a_latex
from src.backend.resolutores.operaciones_matrices.formateadores import (
    matriz_a_latex, sumar_restar_matriz_a_latex, multiplicar_matriz_a_latex,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def test_fraccion_textual_conserva_denominador_mayor_que_mil():
    """La fracción no se aproxima al denominador límite."""
    assert formatear_fraccion_texto(Fraction(1, 1001)) == "1/1001"


def test_fraccion_textual_conserva_denominador_largo():
    """El numerador y denominador se mantienen en el texto."""
    assert formatear_fraccion_texto(Fraction(123, 4567)) == "123/4567"


def test_fraccion_textual_muestra_enteros_sin_denominador():
    """Los enteros y el cero se representan sin fracción explícita."""
    assert formatear_fraccion_texto(Fraction(5, 1)) == "5"
    assert formatear_fraccion_texto(5) == "5"
    assert formatear_fraccion_texto(Fraction(0)) == "0"


def test_fraccion_textual_conserva_fracciones_simples():
    """Las fracciones positivas y negativas conservan sus signos."""
    assert formatear_fraccion_texto(Fraction(1, 7)) == "1/7"
    assert formatear_fraccion_texto(Fraction(-3, 2)) == "-3/2"


def test_fraccion_textual_recupera_flotantes_simples():
    """El formato aproxima flotantes a las fracciones simples esperadas."""
    assert formatear_fraccion_texto(0.5) == "1/2"
    assert formatear_fraccion_texto(0.33333) == "1/3"


def test_numero_latex_conserva_fraccion_exacta():
    """El formato LaTeX conserva el denominador original."""
    assert numero_a_latex(Fraction(1, 101)) == r"\frac{1}{101}"


def test_numero_latex_conserva_denominador_mayor_que_mil():
    """El denominador grande se muestra completo."""
    assert numero_a_latex(Fraction(1, 1001)) == r"\frac{1}{1001}"


def test_numero_latex_muestra_enteros_sin_denominador():
    """Los enteros y ceros no muestran un denominador unitario."""
    assert numero_a_latex(Fraction(5, 1)) == "5"
    assert numero_a_latex(0) == "0"
    assert numero_a_latex(Fraction(0)) == "0"


def test_numero_latex_conserva_signo_negativo():
    """El signo negativo precede a la fracción LaTeX."""
    assert numero_a_latex(Fraction(-2, 3)) == r"-\frac{2}{3}"


def test_numero_latex_recupera_flotante_simple():
    """El flotante medio se representa como fracción simple."""
    assert numero_a_latex(0.5) == r"\frac{1}{2}"


def test_solucion_gauss_conserva_denominador_grande_en_texto():
    """La solución escrita conserva el denominador del sistema."""
    resolutor = ResolutorGauss(Matriz(1, 2, [[1001, 1]]))
    resultado = resolutor.resolver()
    assert resultado["solucion"] == ["1/1001"]


def test_solucion_gauss_conserva_fraccion_simple_en_texto():
    """El formato de la solución conserva la fracción reducida."""
    resolutor = ResolutorGauss(Matriz(1, 2, [[7, 2]]))
    resultado = resolutor.resolver()
    assert resultado["solucion"] == ["2/7"]


def test_matriz_latex_utiliza_llaves_simples():
    """El entorno matricial tiene apertura y cierre válidos."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    contenido = matriz_a_latex(matriz)
    assert r"\begin{bmatrix}" in contenido
    assert r"\end{bmatrix}" in contenido
    assert "{{" not in contenido
    assert "}}" not in contenido


def test_suma_y_resta_latex_utilizan_llaves_simples():
    """Las matrices de ambas operaciones usan entornos válidos."""
    matriz_a = Matriz(2, 2, [[1, -2], [3, 4]])
    matriz_b = Matriz(2, 2, [[5, 6], [-7, 8]])
    suma = sumar_restar_matriz_a_latex(matriz_a, matriz_b, "+")
    resta = sumar_restar_matriz_a_latex(matriz_a, matriz_b, "-")
    for contenido in (suma, resta):
        assert r"\begin{bmatrix}" in contenido
        assert r"\end{bmatrix}" in contenido
        assert "{{" not in contenido
        assert "}}" not in contenido


def test_producto_matricial_latex_utiliza_llaves_simples():
    """Los entornos de matrices del producto no duplican llaves."""
    matriz_a = Matriz(2, 2, [[1, 2], [3, 4]])
    matriz_b = Matriz(2, 2, [[5, 6], [7, 8]])
    contenido = multiplicar_matriz_a_latex(matriz_a, matriz_b)
    assert r"\begin{bmatrix}" in contenido
    assert r"\end{bmatrix}" in contenido
    assert "{{" not in contenido
    assert "}}" not in contenido
