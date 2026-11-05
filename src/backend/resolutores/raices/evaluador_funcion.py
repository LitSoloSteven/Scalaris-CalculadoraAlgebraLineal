"""Evaluación segura de expresiones reales mediante una gramática AST acotada."""
import ast
from collections.abc import Callable

from .gramatica_funcion import analizar_expresion, FUNCIONES_REALES, CONSTANTES_REALES
from .operaciones_reales import aplicar_funcion, aplicar_operador, comprobar_real, ejecutar_operacion
from .unidades_angulares import validar_unidad_angular

FUNCIONES_PERMITIDAS = {**FUNCIONES_REALES, **CONSTANTES_REALES}


def compilar(expresion: str, *, unidad_angular: str = "radianes") -> Callable[[float], float]:
    """Valida una expresión y devuelve f(x); lanza ValueError o ErrorNoFinito si es inválida."""
    unidad = validar_unidad_angular(unidad_angular)
    arbol = analizar_expresion(expresion)

    def funcion(valor: float) -> float:
        """Evalúa la expresión con argumento finito y errores de dominio controlados."""
        return _evaluar_nodo(arbol.body, comprobar_real(valor), unidad)

    return funcion


def evaluar(funcion: Callable[[float], float], valor: float) -> float:
    """Devuelve f(valor) finito; lanza ErrorDominio o ErrorNoFinito para fallos numéricos."""
    argumento = comprobar_real(valor)
    return ejecutar_operacion(lambda: funcion(argumento))


def _evaluar_nodo(nodo: ast.AST, valor: float, unidad: str) -> float:
    if isinstance(nodo, ast.Constant):
        return comprobar_real(nodo.value)
    if isinstance(nodo, ast.Name):
        return valor if nodo.id == "x" else CONSTANTES_REALES[nodo.id]
    if isinstance(nodo, ast.UnaryOp):
        operando = _evaluar_nodo(nodo.operand, valor, unidad)
        return -operando if isinstance(nodo.op, ast.USub) else operando
    if isinstance(nodo, ast.BinOp):
        return aplicar_operador(nodo.op, _evaluar_nodo(nodo.left, valor, unidad), _evaluar_nodo(nodo.right, valor, unidad))
    if isinstance(nodo, ast.Call):
        return aplicar_funcion(nodo.func.id, _evaluar_nodo(nodo.args[0], valor, unidad), unidad_angular=unidad)
    raise ValueError("La expresión contiene un nodo no evaluable.")
