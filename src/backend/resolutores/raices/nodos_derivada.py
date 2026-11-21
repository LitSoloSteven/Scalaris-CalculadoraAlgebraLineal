"""Nodos de expresión usados para construir una derivada simbólica."""
import ast

from .constantes_funcion import CONSTANTES_REALES
from .notacion_calculo import GUARDIA_DERIVADA


def depende_de_x(nodo: ast.AST) -> bool:
    """Determina si el subárbol contiene la variable de derivación."""
    return any(isinstance(hijo, ast.Name) and hijo.id == "x" for hijo in ast.walk(nodo))


def constante(valor: int | float) -> ast.Constant:
    """Representa con un entero los flotantes de valor entero."""
    if isinstance(valor, float) and valor.is_integer():
        return ast.Constant(value=int(valor))
    return ast.Constant(value=valor)


def llamada(nombre: str, argumento: ast.AST) -> ast.Call:
    """Construye una llamada a una función de un argumento."""
    return ast.Call(func=ast.Name(id=nombre, ctx=ast.Load()), args=[argumento], keywords=[])


def proteger_derivada(original: ast.AST, derivada: ast.AST) -> ast.Call:
    """Construye un nodo que comprueba el dominio original antes de devolver la derivada."""
    return ast.Call(
        func=ast.Name(id=GUARDIA_DERIVADA, ctx=ast.Load()), args=[original, derivada], keywords=[],
    )


def valor_constante(nodo: ast.AST) -> int | float | None:
    """Devuelve el valor numérico de un literal o de una constante nombrada."""
    if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
        return nodo.value
    if isinstance(nodo, ast.Name) and nodo.id in CONSTANTES_REALES:
        return CONSTANTES_REALES[nodo.id]
    return None
