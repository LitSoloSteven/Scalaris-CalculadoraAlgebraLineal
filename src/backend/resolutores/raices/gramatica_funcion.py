"""Gramática acotada de expresiones reales de una variable, sin ejecutar código."""
import ast
import math
from decimal import Decimal

from .contrato_biseccion import LONGITUD_MAXIMA_EXPRESION
from .errores_numericos import ErrorCapacidadNumerica

FUNCIONES_REALES = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "exp": math.exp,
                   "log": math.log, "sqrt": math.sqrt, "abs": abs}
CONSTANTES_REALES = {"pi": math.pi, "e": math.e}
MAXIMO_NODOS_EXPRESION = 256
MAXIMA_PROFUNDIDAD_EXPRESION = 32
_OPERADORES = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)


def analizar_expresion(expresion: str) -> ast.Expression:
    """Valida sintaxis y recursos; devuelve AST o lanza ValueError/ErrorNoFinito."""
    if not isinstance(expresion, str) or not expresion.strip():
        raise ValueError("La expresión f(x) es obligatoria.")
    if len(expresion) > LONGITUD_MAXIMA_EXPRESION:
        raise ValueError(f"La expresión excede {LONGITUD_MAXIMA_EXPRESION} caracteres.")
    try:
        arbol = ast.parse(expresion.strip(), mode="eval")
    except (SyntaxError, RecursionError) as error:
        raise ValueError("Sintaxis inválida. Revisa operadores, paréntesis y llamadas a funciones.") from error
    if sum(1 for _ in ast.walk(arbol)) > MAXIMO_NODOS_EXPRESION:
        raise ValueError("La expresión contiene demasiadas operaciones.")
    _validar_nodo(arbol.body, 0)
    _comprobar_literales(arbol, expresion.strip())
    return arbol


def _validar_nodo(nodo: ast.AST, profundidad: int) -> None:
    if profundidad > MAXIMA_PROFUNDIDAD_EXPRESION:
        raise ValueError("La expresión contiene demasiados niveles de operaciones.")
    if isinstance(nodo, ast.Constant):
        _validar_constante(nodo.value)
    elif isinstance(nodo, ast.Name):
        if nodo.id != "x" and nodo.id not in CONSTANTES_REALES:
            raise ValueError(f"Nombre no permitido como valor: {nodo.id}. Las funciones requieren un argumento.")
    elif isinstance(nodo, ast.BinOp) and isinstance(nodo.op, _OPERADORES):
        _validar_nodo(nodo.left, profundidad + 1)
        _validar_nodo(nodo.right, profundidad + 1)
    elif isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
        _validar_nodo(nodo.operand, profundidad + 1)
    elif isinstance(nodo, ast.Call):
        _validar_llamada(nodo, profundidad)
    else:
        raise ValueError("La expresión contiene una operación no permitida.")


def _validar_llamada(nodo: ast.Call, profundidad: int) -> None:
    if not isinstance(nodo.func, ast.Name) or nodo.func.id not in FUNCIONES_REALES:
        raise ValueError("Llamada no permitida. Usa una función real del catálogo.")
    if len(nodo.args) != 1 or nodo.keywords:
        raise ValueError(f"{nodo.func.id} requiere exactamente un argumento, sin nombres de parámetros.")
    _validar_nodo(nodo.args[0], profundidad + 1)


def _validar_constante(valor: object) -> None:
    if type(valor) not in (int, float):
        raise ValueError("Las constantes deben ser números reales; no se admiten textos, booleanos ni complejos.")
    try:
        finito = math.isfinite(float(valor))
    except OverflowError as error:
        raise ErrorCapacidadNumerica("La constante excede la capacidad numérica.") from error
    if not finito:
        raise ErrorCapacidadNumerica("La constante debe ser finita y representable.")


def _comprobar_literales(arbol: ast.Expression, expresion: str) -> None:
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, float) and nodo.value == 0:
            literal = ast.get_source_segment(expresion, nodo)
            if literal is not None and Decimal(literal) != 0:
                raise ErrorCapacidadNumerica("La constante se redondea a cero por subdesbordamiento.", "SUBDESBORDAMIENTO")
