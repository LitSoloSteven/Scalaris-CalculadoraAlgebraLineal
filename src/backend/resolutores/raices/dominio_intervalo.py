"""Detección estructural de polos y restricciones de dominio en argumentos afines."""
import ast
from fractions import Fraction

from src.backend.excepciones import ErrorDominio
from .errores_numericos import ErrorSingularidad
from .gramatica_funcion import analizar_expresion, CONSTANTES_REALES

Afin = tuple[Fraction, Fraction]


def comprobar_dominio_intervalo(expresion: str, intervalo: tuple[float, float]) -> None:
    """Rechaza polos verificables; no certifica continuidad de expresiones generales."""
    arbol = analizar_expresion(expresion)
    extremos = tuple(Fraction(valor) for valor in intervalo)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.BinOp):
            _comprobar_operacion(nodo, extremos)
        elif isinstance(nodo, ast.Call):
            _comprobar_funcion(nodo, extremos)


def _comprobar_operacion(nodo: ast.BinOp, extremos: tuple) -> None:
    if isinstance(nodo.op, ast.Div) and _contiene_cero(nodo.right, extremos):
        raise ErrorSingularidad("División por cero: el denominador se anula dentro del intervalo.")
    if isinstance(nodo.op, ast.Pow):
        exponente = _como_afin(nodo.right)
        if exponente is not None and exponente[0] == 0:
            _comprobar_potencia(nodo.left, exponente[1], extremos)


def _comprobar_potencia(base: ast.AST, exponente: Fraction, extremos: tuple) -> None:
    if exponente < 0 and _contiene_cero(base, extremos):
        raise ErrorSingularidad("División por cero: una potencia negativa tiene base nula en el intervalo.")
    rango = _rango_afin(base, extremos)
    if rango is not None and exponente.denominator != 1 and rango[0] < 0:
        raise ErrorDominio("La potencia no es real para una base negativa en el intervalo.")


def _comprobar_funcion(nodo: ast.Call, extremos: tuple) -> None:
    nombre = nodo.func.id
    rango = _rango_afin(nodo.args[0], extremos)
    if rango is None:
        return
    if nombre == "log" and rango[0] <= 0:
        raise ErrorDominio("El logaritmo no es real o no está definido en todo el intervalo.")
    if nombre == "sqrt" and rango[0] < 0:
        raise ErrorDominio("La raíz cuadrada no es real en todo el intervalo.")


def _contiene_cero(nodo: ast.AST, extremos: tuple) -> bool:
    rango = _rango_afin(nodo, extremos)
    if rango is not None:
        return rango[0] <= 0 <= rango[1]
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Mult):
        return _contiene_cero(nodo.left, extremos) or _contiene_cero(nodo.right, extremos)
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Pow):
        return _potencia_contiene_cero(nodo, extremos)
    if isinstance(nodo, ast.Call) and nodo.func.id == "abs":
        return _contiene_cero(nodo.args[0], extremos)
    return False


def _potencia_contiene_cero(nodo: ast.BinOp, extremos: tuple) -> bool:
    exponente = _como_afin(nodo.right)
    if exponente is None or exponente[0] != 0 or exponente[1] <= 0:
        return False
    return _contiene_cero(nodo.left, extremos)


def _rango_afin(nodo: ast.AST, extremos: tuple) -> tuple | None:
    afin = _como_afin(nodo)
    if afin is None:
        return None
    valores = tuple(afin[0] * extremo + afin[1] for extremo in extremos)
    return min(valores), max(valores)


def _como_afin(nodo: ast.AST) -> Afin | None:
    if isinstance(nodo, ast.Constant):
        return Fraction(0), Fraction(nodo.value)
    if isinstance(nodo, ast.Name):
        return (Fraction(1), Fraction(0)) if nodo.id == "x" else (Fraction(0), Fraction(CONSTANTES_REALES[nodo.id]))
    if isinstance(nodo, ast.UnaryOp):
        afin = _como_afin(nodo.operand)
        signo = -1 if isinstance(nodo.op, ast.USub) else 1
        return None if afin is None else (signo * afin[0], signo * afin[1])
    if isinstance(nodo, ast.BinOp):
        return _combinar_afines(nodo.op, _como_afin(nodo.left), _como_afin(nodo.right))
    return None


def _combinar_afines(operador: ast.operator, izquierda: Afin | None, derecha: Afin | None) -> Afin | None:
    if izquierda is None or derecha is None:
        return None
    if isinstance(operador, (ast.Add, ast.Sub)):
        signo = -1 if isinstance(operador, ast.Sub) else 1
        return izquierda[0] + signo * derecha[0], izquierda[1] + signo * derecha[1]
    if isinstance(operador, ast.Mult):
        return _multiplicar_afines(izquierda, derecha)
    if isinstance(operador, ast.Div) and derecha[0] == 0 and derecha[1] != 0:
        return izquierda[0] / derecha[1], izquierda[1] / derecha[1]
    if isinstance(operador, ast.Pow):
        return _potencia_afin(izquierda, derecha)
    return None


def _potencia_afin(base: Afin, exponente: Afin) -> Afin | None:
    if exponente == (0, 1):
        return base
    if exponente == (0, 0):
        return Fraction(0), Fraction(1)
    return None


def _multiplicar_afines(izquierda: Afin, derecha: Afin) -> Afin | None:
    if izquierda[0] == 0:
        return izquierda[1] * derecha[0], izquierda[1] * derecha[1]
    if derecha[0] == 0:
        return derecha[1] * izquierda[0], derecha[1] * izquierda[1]
    return None
