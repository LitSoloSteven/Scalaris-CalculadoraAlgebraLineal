"""Conversión angular aislada y semántica real del evaluador sin estado global."""
import math
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.gramatica_funcion import CONSTANTES_REALES
from src.backend.resolutores.raices.unidades_angulares import validar_unidad_angular


@pytest.mark.parametrize("expresion, esperado", [
    ("sin(30)", .5), ("cos(60)", .5), ("tan(45)", 1),
    ("asin(.5)", 30), ("acos(.5)", 60), ("atan(1)", 45),
    ("sin(asin(.5))", .5), ("cos(acos(.5))", .5), ("tan(atan(1))", 1),
    ("sin(2x)", .5), ("2sin(x)", 2 * math.sin(math.radians(15))),
])
def test_grados_directas_inversas_y_composicion(expresion, esperado):
    """Convierte cada llamada angular del AST una sola vez, incluidas composiciones y productos."""
    assert evaluar(compilar(expresion, unidad_angular="grados"), 15) == pytest.approx(esperado)


@pytest.mark.parametrize("nombre", ["sin", "cos", "tan", "asin", "acos", "atan"])
def test_radianes_predeterminados_y_explicitos(nombre):
    """La llamada heredada y radianes explícitos mantienen el valor exacto de math."""
    expresion = f"{nombre}(x)"
    esperado = getattr(math, nombre)(.3)
    assert evaluar(compilar(expresion), .3) == esperado
    assert evaluar(compilar(expresion, unidad_angular="radianes"), .3) == esperado


@pytest.mark.parametrize("expresion", [
    "sinh(x)", "cosh(x)", "tanh(x)", "exp(x)", "sqrt(x)", "abs(-x)",
    "log(x)", "ln(x)", "log10(x)", "log2(x)", "pi", "e", "x²+2x-1",
])
def test_funciones_y_constantes_sin_conversion(expresion):
    """La unidad no convierte la variable completa, hiperbólicas ni constantes matemáticas."""
    assert evaluar(compilar(expresion, unidad_angular="grados"), .3) == evaluar(compilar(expresion), .3)
    assert CONSTANTES_REALES == {"pi": math.pi, "e": math.e}


@pytest.mark.parametrize("unidad", [None, True, 1, [], {}, "", "Grados", "deg", "rad", "grados ", "x" * 10000])
def test_unidad_invalida_se_rechaza_antes_de_evaluar(unidad):
    """No se coerciona una unidad ajena ni se acepta en funciones sin trigonometría."""
    with pytest.raises(ValueError, match="unidad angular"):
        validar_unidad_angular(unidad)
    with pytest.raises(ValueError):
        compilar("x", unidad_angular=unidad)
    with pytest.raises(ValueError):
        comprobar_dominio_intervalo("x", (0, 1), unidad_angular=unidad)


@pytest.mark.parametrize("nombre", ["sin", "cos", "tan"])
def test_conversion_no_crea_cero_por_subdesbordamiento(nombre):
    """Rechaza perder un ángulo no nulo incluso si cos parecería evaluar correctamente a uno."""
    with pytest.raises(ErrorNoFinito) as fallo:
        evaluar(compilar(f"{nombre}(x)", unidad_angular="grados"), math.ulp(0.0))
    assert fallo.value.codigo == "SUBDESBORDAMIENTO"


@pytest.mark.parametrize("expresion", ["asin(1.1)", "acos(-1.1)", "(-8)^(1/3)", "sqrt(-1)"])
def test_dominio_real_no_depende_de_unidad(expresion):
    """La conversión angular no evita controles de argumento ni inventa raíces reales."""
    for unidad in ("grados", "radianes"):
        with pytest.raises(ErrorDominio):
            evaluar(compilar(expresion, unidad_angular=unidad), 0)


def test_compilaciones_concurrentes_no_comparten_unidad():
    """Funciones en ambas unidades se intercalan en varios hilos sin contaminar resultados."""
    grados = compilar("sin(x)", unidad_angular="grados")
    radianes = compilar("sin(x)")
    solicitudes = [(grados, 30), (radianes, math.pi / 6)] * 30
    with ThreadPoolExecutor(max_workers=4) as ejecutor:
        resultados = list(ejecutor.map(lambda solicitud: evaluar(*solicitud), solicitudes))
    assert resultados == pytest.approx([.5] * 60)
    assert evaluar(grados, math.pi / 6) != evaluar(radianes, math.pi / 6)


def test_conversion_extrema_y_ausencia_de_cero_forzado():
    """Un ángulo grande finito no desborda al convertirlo y sin(180) conserva su residuo flotante."""
    funcion = compilar("sin(x)", unidad_angular="grados")
    assert evaluar(funcion, 1e308) == math.sin(math.radians(1e308))
    assert evaluar(funcion, 180) == math.sin(math.pi) != 0
