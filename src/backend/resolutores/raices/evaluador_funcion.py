"""Evaluador seguro de funciones reales mediante validación AST."""
import ast
import math
from typing import Callable

from src.backend.excepciones import ErrorDominio, ErrorNoFinito

FUNCIONES_PERMITIDAS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "exp": math.exp, "log": math.log, "sqrt": math.sqrt,
    "abs": abs, "pi": math.pi, "e": math.e,
}

OPERADORES_BINARIOS = {
    ast.Add: lambda izquierdo, derecho: izquierdo + derecho,
    ast.Sub: lambda izquierdo, derecho: izquierdo - derecho,
    ast.Mult: lambda izquierdo, derecho: izquierdo * derecho,
    ast.Pow: lambda izquierdo, derecho: izquierdo ** derecho,
}


def compilar(expresion: str) -> Callable[[float], float]:
    """Devuelve una función segura f(valor) a partir del texto de la expresión."""
    try:
        arbol = ast.parse(expresion, mode="eval")
    except SyntaxError as error:
        raise ValueError(f"Sintaxis inválida: {error.msg}") from error
    _validar_nodos(arbol)

    def funcion(valor: float) -> float:
        """Evalúa el árbol ya compilado en el punto valor."""
        return _evaluar_nodo(arbol.body, valor)

    return funcion


def _validar_nodos(nodo: ast.AST) -> None:
    permitidos = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name,
        ast.Load, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
        ast.USub, ast.UAdd,
    )
    for hijo in ast.walk(nodo):
        if not isinstance(hijo, permitidos):
            raise ValueError(f"Nodo no permitido: {type(hijo).__name__}")
        if isinstance(hijo, ast.Name) and hijo.id != "x" and hijo.id not in FUNCIONES_PERMITIDAS:
            raise ValueError(f"Nombre no permitido: {hijo.id}")
        if isinstance(hijo, ast.Call):
            if not isinstance(hijo.func, ast.Name) or hijo.func.id not in FUNCIONES_PERMITIDAS:
                raise ValueError("Llamada a función no permitida.")


def evaluar(funcion: Callable[[float], float], valor: float) -> float:
    """Evalúa la función en valor y traduce desbordamiento o no finitos a errores de dominio."""
    try:
        resultado = funcion(valor)
    except OverflowError as error:
        raise ErrorNoFinito("Desbordamiento numérico") from error
    if not math.isfinite(resultado):
        raise ErrorNoFinito(f"El resultado en valor={valor} no es finito.")
    return resultado


def _evaluar_nodo(nodo: ast.AST, valor: float) -> float:
    despacho = {
        ast.Constant: _evaluar_constante,
        ast.Name: _evaluar_nombre,
        ast.UnaryOp: _evaluar_unario,
        ast.BinOp: _evaluar_binario,
        ast.Call: _evaluar_llamada,
    }
    funcion = despacho.get(type(nodo))
    if funcion is None:
        raise ValueError(f"Nodo no evaluable: {type(nodo).__name__}")
    return funcion(nodo, valor)


def _evaluar_constante(nodo: ast.Constant, valor: float) -> float:
    return float(nodo.value)


def _evaluar_nombre(nodo: ast.Name, valor: float) -> float:
    return valor if nodo.id == "x" else float(FUNCIONES_PERMITIDAS[nodo.id])


def _evaluar_unario(nodo: ast.UnaryOp, valor: float) -> float:
    valor = _evaluar_nodo(nodo.operand, valor)
    return -valor if isinstance(nodo.op, ast.USub) else valor


def _evaluar_binario(nodo: ast.BinOp, valor: float) -> float:
    izquierda = _evaluar_nodo(nodo.left, valor)
    derecha = _evaluar_nodo(nodo.right, valor)
    if isinstance(nodo.op, ast.Div):
        try:
            return izquierda / derecha
        except ZeroDivisionError as error:
            raise ErrorDominio("División por cero") from error
    operador = OPERADORES_BINARIOS.get(type(nodo.op))
    if operador is None:
        raise ValueError(f"Operador no evaluable: {type(nodo.op).__name__}")
    return operador(izquierda, derecha)


def _evaluar_llamada(nodo: ast.Call, valor: float) -> float:
    argumentos = [_evaluar_nodo(argumento, valor) for argumento in nodo.args]
    try:
        return FUNCIONES_PERMITIDAS[nodo.func.id](*argumentos)
    except ValueError as error:
        raise ErrorDominio(str(error)) from error