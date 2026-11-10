"""Proyección compartida a TeX de la gramática real validada."""
import ast

from src.backend.resolutores.raices.gramatica_funcion import analizar_expresion
from src.backend.resolutores.raices.normalizacion_funcion import normalizar_expresion

_OPERADORES = {ast.Add: ("+", 1), ast.Sub: ("-", 1), ast.Mult: (r"\cdot", 2)}
_FUNCIONES = {
    "sin": r"\sin", "cos": r"\cos", "tan": r"\tan", "exp": r"\exp",
    "ln": r"\ln", "log": r"\ln", "log10": r"\log_{10}", "log2": r"\log_{2}",
    "asin": r"\arcsin", "acos": r"\arccos", "atan": r"\arctan",
    "sinh": r"\sinh", "cosh": r"\cosh", "tanh": r"\tanh",
}
_ATOMO = 5


def formatear_expresion(expresion: str) -> dict[str, str]:
    """Devuelve TeX de vocabulario fijo y texto normalizado; propaga ValueError."""
    arbol = analizar_expresion(expresion)
    formula, _ = _proyectar(arbol.body)
    return {"latex": f"f(x) = {formula}", "texto": f"f(x) = {normalizar_expresion(expresion)}"}


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
        return _proyectar_llamada(nodo), _ATOMO
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


def _proyectar_llamada(nodo: ast.Call) -> str:
    nombre = nodo.func.id
    argumento, _ = _proyectar(nodo.args[0])
    if nombre == "sqrt":
        return rf"\sqrt{{{argumento}}}"
    if nombre == "abs":
        return rf"\left|{argumento}\right|"
    return rf"{_FUNCIONES[nombre]}\left({argumento}\right)"
