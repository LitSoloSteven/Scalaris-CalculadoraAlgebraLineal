"""Coeficientes y texto explicativo de soluciones paramétricas LaTeX."""
from fractions import Fraction
from src.backend.utilidades.formateadores import formatear_expresion_parametrica
from src.backend.utilidades.validadores import ValidadorMatriz
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def test_coeficiente_fraccionario_utiliza_parentesis():
    """La fracción coeficiente queda delimitada antes del parámetro."""
    assert formatear_expresion_parametrica(Fraction(0), {"t": Fraction(1, 2)}) == "(1/2)t"


def test_coeficiente_fraccionario_negativo_utiliza_parentesis():
    """El signo negativo precede al coeficiente delimitado."""
    assert formatear_expresion_parametrica(Fraction(0), {"t": Fraction(-1, 2)}) == "-(1/2)t"


def test_coeficiente_entero_conserva_formato():
    """El coeficiente entero conserva valor y signo en el término."""
    assert formatear_expresion_parametrica(Fraction(0), {"t": Fraction(2)}) == "2t"
    assert formatear_expresion_parametrica(Fraction(0), {"t": Fraction(-3)}) == "-3t"


def test_coeficientes_unitarios_conservan_signo_sin_numero():
    """Los coeficientes unitarios se representan mediante el signo del término."""
    assert formatear_expresion_parametrica(Fraction(0), {"t": Fraction(1)}) == "t"
    assert formatear_expresion_parametrica(Fraction(0), {"t": Fraction(-1)}) == "-t"


def test_constante_fraccionaria_aislada():
    """La expresión sin parámetros conserva la constante racional."""
    assert formatear_expresion_parametrica(Fraction(1, 2), {}) == "1/2"


def test_constante_fraccionaria_con_termino_parametrico():
    """La expresión mantiene constante, signo y coeficiente fraccionario."""
    resultado = formatear_expresion_parametrica(Fraction(1, 2), {"t": Fraction(-1, 3)})
    assert resultado == "1/2 - (1/3)t"


def test_verificacion_latex_delimita_etiqueta_de_ecuacion():
    """La etiqueta de ecuación se representa como texto dentro del modo matemático."""
    _, informe = ValidadorMatriz.verificar_solucion(
        [[Fraction(7)]], [Fraction(9, 7)], [Fraction(9)], como_latex=True)
    assert r"\text{Ecuación 1: }" in informe[0]


def test_verificacion_latex_delimita_estado_de_resultado():
    """El estado de la comprobación queda delimitado como texto."""
    _, informe = ValidadorMatriz.verificar_solucion(
        [[Fraction(1)]], [Fraction(1)], [Fraction(1)], como_latex=True)
    assert r"\text{Correcto}" in informe[0]


def test_sustitucion_regresiva_delimita_encabezado_de_variables_libres():
    """El encabezado explicativo no se interpreta como una fórmula."""
    matriz = Matriz(1, 4, [[1, 1, 1, 1]])
    resultado = ResolutorGauss(matriz).resolver()
    assert resultado["estado"] == "SOLUCIONES_INFINITAS"
    assert any(paso.startswith(r"\text{Variables libres identificadas: }")
               for paso in resultado["pasos_sustitucion_regresiva"])


def test_sustitucion_regresiva_lineas_de_variables_no_contienen_texto_suelto():
    """Las líneas algebraicas conservan únicamente su contenido matemático."""
    matriz = Matriz(1, 4, [[1, 1, 1, 1]])
    resultado = ResolutorGauss(matriz).resolver()
    lineas_variables = [paso for paso in resultado["pasos_sustitucion_regresiva"] if not paso.startswith(r"\text{")]
    assert len(lineas_variables) >= 1
    for linea in lineas_variables:
        assert "identificadas" not in linea
        assert "libres" not in linea
