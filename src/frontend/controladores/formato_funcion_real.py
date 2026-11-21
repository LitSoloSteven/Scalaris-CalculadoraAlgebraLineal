"""Proyección compartida a TeX de la gramática real validada."""
import ast

from src.backend.resolutores.raices.gramatica_funcion import analizar_expresion
from src.backend.resolutores.raices.normalizacion_funcion import normalizar_expresion
from src.backend.resolutores.raices.notacion_calculo import (
    AGREGADOS, GUARDIA_DERIVADA, NOMBRES_ANGULARES, POSTFIJOS, entero_literal,
)

_OPERADORES = {ast.Add: ("+", 1), ast.Sub: ("-", 1), ast.Mult: (r"\cdot", 2)}
_FUNCIONES = {
    "sin": r"\sin", "cos": r"\cos", "tan": r"\tan", "exp": r"\exp",
    "ln": r"\ln", "log": r"\ln", "log10": r"\log_{10}", "log2": r"\log_{2}",
    "asin": r"\arcsin", "acos": r"\arccos", "atan": r"\arctan",
    "sinh": r"\sinh", "cosh": r"\cosh", "tanh": r"\tanh",
}
_ATOMO = 5
_INDICES_RAIZ = {"sqrt": "", "cbrt": "[3]", "raiz4": "[4]"}
_AGREGADOS = {AGREGADOS["∑"]: r"\sum", AGREGADOS["∏"]: r"\prod"}
_POSTFIJOS = {
    POSTFIJOS["°"]: r"^{\circ}", POSTFIJOS["‰"]: r"\text{‰}",
    POSTFIJOS["′"]: r"^{\prime}", POSTFIJOS["″"]: r"^{\prime\prime}",
}


def formatear_expresion(expresion: str, etiqueta: str = "f(x)") -> dict[str, str]:
    """Devuelve TeX de vocabulario fijo y texto normalizado; propaga ValueError."""
    arbol = analizar_expresion(expresion, conservar_calculo=True)
    formula, _ = _proyectar(arbol.body)
    return {"latex": f"{etiqueta} = {formula}", "texto": f"{etiqueta} = {normalizar_expresion(expresion)}"}


def numero_tex(texto: str) -> str:
    """Convierte una cadena numérica de Python a notación científica de TeX."""
    mantisa, separador, exponente = texto.lower().partition("e")
    return rf"{mantisa}\times 10^{{{int(exponente)}}}" if separador else mantisa


def _proyectar(nodo: ast.AST) -> tuple[str, int]:
    if isinstance(nodo, ast.Constant):
        return numero_tex(str(nodo.value)), 2 if "e" in str(nodo.value) else _ATOMO
    if isinstance(nodo, ast.Name):
        return r"\pi" if nodo.id == "pi" else nodo.id, _ATOMO
    if isinstance(nodo, ast.UnaryOp):
        signo = "-" if isinstance(nodo.op, ast.USub) else "+"
        return signo + _agrupar(_proyectar(nodo.operand), 4), 3
    if isinstance(nodo, ast.Call):
        return _proyectar_llamada(nodo)
    return _proyectar_binario(nodo)


def _proyectar_binario(nodo: ast.BinOp) -> tuple[str, int]:
    izquierda, derecha = _proyectar(nodo.left), _proyectar(nodo.right)
    if isinstance(nodo.op, ast.Div):
        return rf"\frac{{{izquierda[0]}}}{{{derecha[0]}}}", _ATOMO
    if isinstance(nodo.op, ast.Pow):
        return f"{_agrupar(izquierda, _ATOMO)}^{{{derecha[0]}}}", 4
    signo, prioridad = _OPERADORES[type(nodo.op)]
    return f"{_agrupar(izquierda, prioridad)} {signo} {_agrupar(derecha, prioridad + 1)}", prioridad


def _agrupar(proyeccion: tuple[str, int], minima: int) -> str:
    texto, prioridad = proyeccion
    return rf"\left({texto}\right)" if prioridad < minima else texto


def _proyectar_llamada(nodo: ast.Call) -> tuple[str, int]:
    nombre = NOMBRES_ANGULARES.get(nodo.func.id, nodo.func.id)
    if nombre == GUARDIA_DERIVADA:
        return _proyectar(nodo.args[1])
    if nombre in _AGREGADOS:
        return _proyectar_agregado(_AGREGADOS[nombre], nodo), 4
    if nombre in _POSTFIJOS:
        return _proyectar_postfijo(_POSTFIJOS[nombre], nodo.args[0]), 4
    argumento, _ = _proyectar(nodo.args[0])
    if nombre in _INDICES_RAIZ:
        return rf"\sqrt{_INDICES_RAIZ[nombre]}{{{argumento}}}", _ATOMO
    if nombre == "abs":
        return rf"\left|{argumento}\right|", _ATOMO
    return rf"{_FUNCIONES[nombre]}\left({argumento}\right)", _ATOMO


def _proyectar_postfijo(sufijo: str, nodo: ast.AST) -> str:
    prioridad = _ATOMO if isinstance(nodo, (ast.Name, ast.Constant)) else _ATOMO + 1
    return _agrupar(_proyectar(nodo), prioridad) + sufijo


def _proyectar_agregado(operador: str, nodo: ast.Call) -> str:
    indice, inferior, superior, cuerpo = nodo.args
    expresion, _ = _proyectar(cuerpo)
    limites = f"_{{{indice.id}={entero_literal(inferior)}}}^{{{entero_literal(superior)}}}"
    return rf"{operador}{limites}\left({expresion}\right)"
