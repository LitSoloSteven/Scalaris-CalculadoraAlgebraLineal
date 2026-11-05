"""Rechazo de código, límites de recursos y dominio real tras normalizar notación."""
import pytest

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar
from src.backend.resolutores.raices.gramatica_funcion import analizar_expresion
from src.backend.resolutores.raices.normalizacion_funcion import normalizar_expresion


@pytest.mark.parametrize("expresion", [
    "x.real", "(x).__class__", "x[0]", "[x]", "{x}", "{'x':1}", "'x'", '"x"',
    "f'{x}'", "__import__('os')", "open(x)", "eval(x)", "exec(x)", "lambda: x",
    "[x for x in (1,2)]", "(x for x in (1,2))", "import os", "x;1", "x:=1",
    "sin(x=1)", "sin(x,1)", "sin(*x)", "sin(**x)", "sin()", "sin", "pi(1)",
    "e(1)", "funcion(x)", "sinx", "xx", "xp i", "True", "None", "1j",
    "x//2", "x%2", "x<2", "x|2", "x&2", "x # comentario", "ｘ+1", "sіn(x)",
    "1 2", "x 2", "x**", "²x", "x⁴", "sin(x", "x)", "x\n+1",
    "x* *2", "1 .2", "log 10(x)",
])
def test_codigo_y_tokens_no_admitidos(expresion):
    """El catálogo y la lista AST siguen cerrados ante notación maliciosa o ambigua."""
    with pytest.raises(ValueError):
        compilar(expresion)


@pytest.mark.parametrize("expresion", [None, 123, True, "", " ", "x" * 513, " " * 512 + "x"])
def test_forma_y_longitud_original(expresion):
    """Se limita la captura antes de tokenizar, incluso si solo se compone de espacios."""
    with pytest.raises(ValueError):
        normalizar_expresion(expresion)


@pytest.mark.parametrize("expresion", ["(x)" * 129, "x²+" * 120 + "x", "x^1" * 130])
def test_longitud_posterior_a_expansion(expresion):
    """Una captura acotada no puede crecer sin límite al explicitar productos o potencias."""
    assert len(expresion) <= 512
    with pytest.raises(ValueError, match="caracteres"):
        normalizar_expresion(expresion)


@pytest.mark.parametrize("expresion, mensaje", [
    ("x+" * 85 + "x", "operaciones"), ("sin(" * 34 + "x" + ")" * 34, "niveles"),
])
def test_limites_ast_despues_de_normalizacion(expresion, mensaje):
    """El AST normalizado conserva los presupuestos de nodos y profundidad."""
    assert len(normalizar_expresion(expresion)) <= 512
    with pytest.raises(ValueError, match=mensaje):
        analizar_expresion(expresion)


@pytest.mark.parametrize("expresion", ["(-8)^(1/3)", "(-8)**(1/3)", "(-8)^(.3333333333333333)"])
def test_potencia_fraccionaria_negativa_no_inventa_raiz_real(expresion):
    """La aritmética flotante mantiene el rechazo de resultados complejos sin racionalizar."""
    with pytest.raises(ErrorDominio):
        evaluar(compilar(expresion), 0)


@pytest.mark.parametrize("nombre", ["log", "ln", "log10", "log2"])
def test_dominio_estructural_de_logaritmos(nombre):
    """Todos los logaritmos rechazan el mismo argumento afín no positivo."""
    with pytest.raises(ErrorDominio):
        comprobar_dominio_intervalo(f"{nombre}(2x-1)", (0, 1))
    comprobar_dominio_intervalo(f"{nombre}(2x-1)", (1, 2))


@pytest.mark.parametrize("nombre", ["asin", "acos"])
def test_dominio_estructural_de_inversas(nombre):
    """Las inversas admiten sus fronteras y rechazan argumentos fuera de [-1,1]."""
    comprobar_dominio_intervalo(f"{nombre}(2x-1)", (0, 1))
    with pytest.raises(ErrorDominio):
        comprobar_dominio_intervalo(f"{nombre}(2x-1)", (-.1, 1))
    with pytest.raises(ErrorDominio):
        evaluar(compilar(f"{nombre}(x)"), 1.1)


@pytest.mark.parametrize("expresion", ["sinh(1000)", "cosh(1000)", "1e309x"])
def test_capacidad_numerica_del_catalogo(expresion):
    """Las funciones nuevas y la notación implícita conservan errores numéricos controlados."""
    with pytest.raises(ErrorNoFinito):
        evaluar(compilar(expresion), 1)
