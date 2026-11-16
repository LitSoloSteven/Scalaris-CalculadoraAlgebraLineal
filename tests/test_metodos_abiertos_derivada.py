"""Derivada simbólica sobre el AST de la gramática: reglas, simplificación y límites."""
import math

import pytest

from src.backend.excepciones import ErrorDominio
from src.backend.resolutores.raices.evaluador_funcion import compilar
from src.backend.resolutores.raices.metodos_abiertos import derivar_expresion


def _evaluar_derivada(expresion, x):
    return compilar(derivar_expresion(expresion))(x)


def _producto_balanceado(cantidad):
    factores = ["x"] * cantidad
    while len(factores) > 1:
        factores = [
            f"({factores[i]}*{factores[i + 1]})"
            for i in range(0, len(factores), 2)
        ]
    return factores[0]


@pytest.mark.parametrize(
    "expresion,x,esperado",
    [
        ("x^3 - x - 2", 1.5, 5.75),
        ("x^3 - 2*x - 5", 2.0, 10.0),
        ("x^2 + 3*x - 1", 0.5, 4.0),
        ("1/x", 2.0, -0.25),
        ("sqrt(x)", 4.0, 0.25),
        ("sin(x)", 0.0, 1.0),
        ("cos(x)", 0.0, 0.0),
        ("tan(x)", 0.0, 1.0),
        ("asin(x)", 0.0, 1.0),
        ("acos(x)", 0.0, -1.0),
        ("atan(x)", 0.0, 1.0),
        ("sinh(x)", 0.0, 1.0),
        ("cosh(x)", 0.0, 0.0),
        ("tanh(x)", 0.0, 1.0),
        ("exp(x)", 0.0, 1.0),
        ("ln(x)", 1.0, 1.0),
        ("log(x)", 1.0, 1.0),
        ("log10(x)", 1.0, 1.0 / math.log(10)),
        ("log2(x)", 1.0, 1.0 / math.log(2)),
        ("abs(x)", 2.0, 1.0),
        ("abs(x)", -2.0, -1.0),
        ("2^x", 3.0, 8.0 * math.log(2)),
        ("pi*x + e", 7.0, math.pi),
    ],
)
def test_derivada_coincide_con_la_formula(expresion, x, esperado):
    """La derivada compilada reproduce la regla matemática en el punto pedido."""
    assert _evaluar_derivada(expresion, x) == pytest.approx(esperado, rel=1e-12, abs=1e-12)


def test_derivada_de_sin_en_pi_medios_es_cero():
    """cos(pi/2) se redondea a cero dentro de la tolerancia numérica."""
    assert _evaluar_derivada("sin(x)", math.pi / 2) == pytest.approx(0.0, abs=1e-15)


def test_derivada_de_abs_no_existe_en_cero():
    """La regla x/abs(x) no se puede evaluar en el punto singular."""
    with pytest.raises(ErrorDominio):
        _evaluar_derivada("abs(x)", 0.0)


def test_potencia_con_base_y_exponente_variables_no_soportada():
    """x^x requiere una regla logarítmica fuera del alcance de la v1."""
    with pytest.raises(ValueError, match="potencia con base y exponente variables"):
        derivar_expresion("x^x")


def test_expresion_invalida_propaga_error_de_gramatica():
    """La sintaxis se valida antes de intentar derivar."""
    with pytest.raises(ValueError):
        derivar_expresion("x +")


def test_derivada_demasiado_grande_falla_con_mensaje_claro():
    """Un producto balanceado grande desborda los límites de la gramática derivada."""
    expresion = _producto_balanceado(64)
    with pytest.raises(ValueError, match="derivada simbólica excede"):
        derivar_expresion(expresion)


def test_derivada_no_modifica_la_expresion_de_entrada():
    """La cadena original queda intacta tras derivar."""
    expresion = "x^3 - x - 2"
    derivar_expresion(expresion)
    assert expresion == "x^3 - x - 2"
