"""Contratos de captura, evaluación, dominio y presentación del cálculo tipográfico."""

import math

import pytest

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.evaluador_funcion import compilar
from src.backend.resolutores.raices.metodos_abiertos import derivar_expresion
from src.backend.resolutores.raices.normalizacion_funcion import normalizar_expresion
from src.frontend.controladores.captura_real import real_capturado
from src.frontend.controladores.formato_funcion_real import formatear_expresion
from src.frontend.controladores.metodos_abiertos import resolver_captura


@pytest.mark.parametrize(("texto", "esperado"), [
    ("π÷2", math.pi / 2), ("ℯ⁻¹", 1 / math.e), ("√(9)×∛(−8)·∜(16)", -12),
    ("−⅝+1⁄2+3∕4", .625), ("180°", math.pi), ("250‰", .25),
    ("2²‰", .004), ("001.5", 1.5), ("1e-200", 1e-200),
])
def test_captura_real_evalua_constantes(texto, esperado):
    """Convierte símbolos y conserva la captura de números escritos como texto."""
    assert real_capturado(texto, "El extremo") == pytest.approx(esperado)


@pytest.mark.parametrize("texto", ["x-x", "(2)′", "∑(i,1,2,i)", "∫(0,1,x)", "∞", "√(−1)", "1÷0", "1e-400"])
def test_captura_real_rechaza_calculo_variable_o_no_representable(texto):
    """Reporta el campo cuando la expresión excede su perfil o su dominio."""
    with pytest.raises(ValueError, match="El extremo debe ser un número real"):
        real_capturado(texto, "El extremo")


@pytest.mark.parametrize(("texto", "valor", "esperado"), [
    ("∑(i,−1,2,i×x)", 3, 6), ("∏(k,1,3,k+x)", 2, 60),
    ("∑(i,1,2,i+∑(i,1,2,i))", 0, 9),
    ("∑(i,1,2,∏(j,1,2,i+j+x))", 1, 32),
    ("2∑(i,1,3,i)x", 2, 24), ("∑(i,0,0,x)", 2, 2),
    ("x³′", 2, 12), ("x^−2′", 2, -.25), ("(x³+x)″", 2, 12),
    ("∏(i,1,3,x-i)′", 2, -1), ("(250‰x)′", 2, .25), ("(x°)′", 2, math.pi / 180),
])
def test_evaluacion_y_normalizacion_son_coherentes(texto, valor, esperado):
    """Evalúa agregados, alcances, derivadas, potencias y multiplicación implícita."""
    normalizada = normalizar_expresion(texto)
    assert compilar(texto)(valor) == pytest.approx(esperado)
    assert compilar(normalizada)(valor) == pytest.approx(esperado)
    assert normalizar_expresion(normalizada) == normalizada


@pytest.mark.parametrize(("texto", "esperado"), [
    ("sin(30°)", .5), ("sin(30)", .5), ("sin(x)′", math.sqrt(3) / 2 * math.pi / 180),
    ("sin(x°)″", -.5 * (math.pi / 180) ** 2),
    ("asin(x/60)′", (180 / math.pi) / (60 * math.sqrt(.75))),
    ("cos(sin(30°))", math.cos(math.radians(.5))),
])
def test_trigonometria_en_grados_reconoce_sufijos_y_derivadas(texto, esperado):
    """Distingue los grados explícitos de la unidad configurada y aplica la regla de la cadena."""
    assert compilar(texto, unidad_angular="grados")(30) == pytest.approx(esperado)
    assert compilar("sin(30°)", unidad_angular="radianes")(30) == pytest.approx(.5)


@pytest.mark.parametrize("texto", [
    "∑(i,1,3,i)+i", "∑(x,1,3,x)", "∑(i,1,x,i)", "∑(i,3,1,i)", "∏(i,1,33,i)",
    "∑(i,1,32,∏(j,1,32,x+i+j))", "∑(i,1,3,(i,x))", "∑(i,1,3,i,)",
    "sin(x,)", "°", "(x^x)′", "∫(0,1,x)", "∞",
])
def test_calculo_fuera_de_la_gramatica_o_presupuesto(texto):
    """La evaluación y la vista previa rechazan las mismas entradas inválidas."""
    with pytest.raises(ValueError):
        compilar(texto)
    with pytest.raises(ValueError):
        formatear_expresion(texto)


def test_agregados_preservan_los_errores_numericos_por_termino():
    """La reducción propaga el dominio y la pérdida total de un término."""
    with pytest.raises(ErrorDominio):
        compilar("∑(i,1,3,1/(x-i))")(2)
    with pytest.raises(ErrorNoFinito, match="subdesbordamiento"):
        compilar("∏(i,1,2,1e-200x)")(1)
    with pytest.raises(ErrorDominio, match="tangente"):
        comprobar_dominio_intervalo("tan(x°)", (89, 91), unidad_angular="grados")


def test_vista_previa_proyecta_operadores_y_agrupa_potencias():
    """Genera límites, primas, grado y por mil usando comandos TeX fijos."""
    texto = "∑(i,1,3,i×x) + ∏(j,-1,2,j+x) + (x²)′ + (x³)″ + 30° + 250‰"
    formula = formatear_expresion(texto)["latex"]
    for simbolo in (r"\sum_{i=1}^{3}", r"\prod_{j=-1}^{2}", r"^{\prime}", r"^{\prime\prime}", r"^{\circ}", "‰"):
        assert simbolo in formula
    assert formatear_expresion("(30°)^2")["latex"] == r"f(x) = \left(30^{\circ}\right)^{2}"


def test_derivacion_y_resolucion_desde_la_captura():
    """Newton recibe un extremo real, deriva un agregado y converge a la raíz esperada."""
    texto = "∑(i,1,3,i×x) + ∏(i,1,2,x+i) - (x³)′ - 9"
    assert compilar(derivar_expresion(texto))(1) == pytest.approx(5)
    resultado = resolver_captura({"metodo": "newton", "expresion": texto, "x0": "√(.64)"})
    assert resultado["estado"] == "EXITO"
    assert resultado["raiz"] == pytest.approx(1)
