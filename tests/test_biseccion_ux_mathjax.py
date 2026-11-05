"""Proyección segura y precedencia de fórmulas de bisección."""
import pytest

from src.backend.resolutores.raices.gramatica_funcion import FUNCIONES_REALES
from src.frontend.controladores.biseccion.formato_expresion import formatear_expresion
from src.frontend.controladores.biseccion.formulas_procedimiento import formulas_iteracion


def test_precedencia_y_fracciones():
    """Distingue signo exterior, base negativa, potencias asociadas y fracciones anidadas."""
    assert formatear_expresion("−x²")["latex"] == "f(x) = -x^{2}"
    assert formatear_expresion("(−x)²")["latex"] == r"f(x) = \left(-x\right)^{2}"
    assert formatear_expresion("(x^2)^3")["latex"] == r"f(x) = \left(x^{2}\right)^{3}"
    assert formatear_expresion("x/(1/(x+1))")["latex"] == r"f(x) = \frac{x}{\frac{1}{x + 1}}"


@pytest.mark.parametrize("nombre", FUNCIONES_REALES)
def test_proyecta_catalogo_real(nombre):
    """Todas las llamadas aceptadas disponen de una representación definida."""
    assert formatear_expresion(f"{nombre}(x)")["latex"].startswith("f(x) = \\")


@pytest.mark.parametrize("expresion", ["sin(", "<img src=x onerror=alert(1)>", r"\require{html}", r"\href{x}{y}"])
def test_rechaza_texto_ajeno_a_gramatica(expresion):
    """El adaptador nunca trata la captura como TeX arbitrario."""
    with pytest.raises(ValueError):
        formatear_expresion(expresion)


def test_punto_medio_usa_valor_publicado():
    """Proyecta las magnitudes de una fila y conserva el punto medio suministrado."""
    fila = {"extremo_izquierdo": 1, "extremo_derecho": 2, "c": 1.499,
            "f_a": -1, "f_b": 2, "f_c": 0.2}
    intervalo, medio, evaluaciones = formulas_iteracion(fila)
    assert intervalo.endswith("[1,2]") and medio.endswith("1.4990000000000001")
    assert "f(a)=-1" in evaluaciones and "f(b)=2" in evaluaciones
