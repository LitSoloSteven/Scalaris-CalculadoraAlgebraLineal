"""Gramática acotada de expresiones reales de una variable, sin ejecutar código."""
import ast
import math
from decimal import Decimal

from .constantes_funcion import CONSTANTES_REALES as CONSTANTES_REALES
from .errores_numericos import ErrorCapacidadNumerica
from .expansion_calculo import desarrollar_calculo
from .nodos_integral import NOMBRE_INTEGRAL, signo_infinito, variable_ligable
from .normalizacion_funcion import normalizar_expresion
from .notacion_calculo import (
    AGREGADOS, DERIVADAS, GUARDIA_DERIVADA, MAXIMO_TERMINOS_AGREGADO, NOMBRES_ANGULARES, POSTFIJOS, entero_literal,
)
from .unidades_angulares import validar_unidad_angular

FUNCIONES_REALES = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "exp": math.exp,
                   "log": math.log, "ln": math.log, "log10": math.log10, "log2": math.log2,
                   "asin": math.asin, "acos": math.acos, "atan": math.atan,
                   "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
                   "sqrt": math.sqrt, "cbrt": math.cbrt, "raiz4": lambda valor: math.sqrt(math.sqrt(valor)),
                   "abs": abs}
MAXIMO_NODOS_EXPRESION = 256
MAXIMA_PROFUNDIDAD_EXPRESION = 32
_OPERADORES = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
_AGREGADOS = frozenset(AGREGADOS.values())
_CALCULO_MULTIPLE = _AGREGADOS | {GUARDIA_DERIVADA, NOMBRE_INTEGRAL}
_CALCULO = _AGREGADOS | frozenset(POSTFIJOS.values())
_FUNCIONES_UNARIAS = frozenset((*FUNCIONES_REALES, *NOMBRES_ANGULARES, *POSTFIJOS.values()))
_VARIABLE_INDEPENDIENTE = frozenset({"x"})


def analizar_expresion(
    expresion: str, *, conservar_calculo: bool = False, solo_constantes: bool = False,
    unidad_angular: str = "radianes",
) -> ast.Expression:
    """Devuelve AST validado para evaluar o proyectar; lanza ValueError/ErrorNoFinito."""
    unidad = validar_unidad_angular(unidad_angular)
    arbol = _leer_expresion(expresion)
    variables = frozenset() if solo_constantes else _VARIABLE_INDEPENDIENTE
    _validar_arbol(arbol, variables)
    if not any(isinstance(nodo, ast.Call) and nodo.func.id in _CALCULO for nodo in ast.walk(arbol)):
        return arbol
    desarrollado = desarrollar_calculo(arbol, MAXIMO_NODOS_EXPRESION, unidad)
    _validar_arbol(desarrollado, variables)
    return arbol if conservar_calculo else desarrollado


def _leer_expresion(expresion: str) -> ast.Expression:
    normalizada = normalizar_expresion(expresion)
    try:
        arbol = ast.parse(normalizada, mode="eval")
    except (SyntaxError, RecursionError) as error:
        raise ValueError("Sintaxis inválida. Revisa operadores, paréntesis y llamadas a funciones.") from error
    _comprobar_literales(arbol, normalizada)
    return arbol


def _validar_arbol(arbol: ast.Expression, variables: frozenset[str]) -> None:
    if sum(1 for _ in ast.walk(arbol)) > MAXIMO_NODOS_EXPRESION:
        raise ValueError("La expresión contiene demasiadas operaciones.")
    _validar_nodo(arbol.body, 0, variables)


def _validar_nodo(nodo: ast.AST, profundidad: int, variables: frozenset[str]) -> None:
    if profundidad > MAXIMA_PROFUNDIDAD_EXPRESION:
        raise ValueError("La expresión contiene demasiados niveles de operaciones.")
    if isinstance(nodo, ast.Constant):
        _validar_constante(nodo.value)
    elif isinstance(nodo, ast.Name):
        if nodo.id not in variables and nodo.id not in CONSTANTES_REALES:
            raise ValueError(f"Nombre no permitido como valor: {nodo.id}. Las funciones requieren un argumento.")
    elif isinstance(nodo, ast.BinOp):
        _validar_binario(nodo, profundidad, variables)
    elif isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
        _validar_nodo(nodo.operand, profundidad + 1, variables)
    elif isinstance(nodo, ast.Call):
        _validar_llamada(nodo, profundidad, variables)
    else:
        raise ValueError("La expresión contiene una operación no permitida.")


def _validar_binario(nodo: ast.BinOp, profundidad: int, variables: frozenset[str]) -> None:
    if not isinstance(nodo.op, _OPERADORES):
        raise ValueError("La expresión contiene un operador no permitido.")
    _validar_nodo(nodo.left, profundidad + 1, variables)
    _validar_nodo(nodo.right, profundidad + 1, variables)


def _validar_llamada(nodo: ast.Call, profundidad: int, variables: frozenset[str]) -> None:
    if not isinstance(nodo.func, ast.Name) or nodo.keywords:
        raise ValueError("Llamada no permitida. Usa una función real del catálogo.")
    nombre = nodo.func.id
    if nombre in _CALCULO_MULTIPLE and "x" in variables:
        _validar_calculo_multiple(nodo, profundidad, variables)
        return
    if nombre not in _FUNCIONES_UNARIAS or (nombre in DERIVADAS and "x" not in variables):
        raise ValueError("Llamada no permitida. Usa una función real del catálogo.")
    if len(nodo.args) != 1:
        raise ValueError(f"{nombre} requiere exactamente un argumento, sin nombres de parámetros.")
    _validar_nodo(nodo.args[0], profundidad + 1, variables)


def _validar_calculo_multiple(nodo: ast.Call, profundidad: int, variables: frozenset[str]) -> None:
    if nodo.func.id == NOMBRE_INTEGRAL:
        _validar_integral(nodo, profundidad, variables)
        return
    if nodo.func.id in _AGREGADOS:
        _validar_agregado(nodo, profundidad, variables)
        return
    if len(nodo.args) != 2:
        raise ValueError("La comprobación de dominio de la derivada requiere dos argumentos.")
    for argumento in nodo.args:
        _validar_nodo(argumento, profundidad + 1, variables)


def _validar_agregado(nodo: ast.Call, profundidad: int, variables: frozenset[str]) -> None:
    if len(nodo.args) != 4:
        raise ValueError("Escribe el índice, el límite inferior, el superior y la expresión.")
    indice, inferior, superior, expresion = nodo.args
    if not variable_ligable(indice):
        raise ValueError("Usa una letra minúscula libre, por ejemplo i, como índice.")
    primero, ultimo = entero_literal(inferior), entero_literal(superior)
    if not 1 <= ultimo - primero + 1 <= MAXIMO_TERMINOS_AGREGADO:
        raise ValueError(f"Usa límites ordenados con un máximo de {MAXIMO_TERMINOS_AGREGADO} términos.")
    _validar_constante(primero)
    _validar_constante(ultimo)
    _validar_nodo(expresion, profundidad + 1, variables | {indice.id})


def _validar_integral(nodo: ast.Call, profundidad: int, variables: frozenset[str]) -> None:
    if len(nodo.args) != 4:
        raise ValueError("Escribe la integral como ∫(expresión, variable, límite inferior, límite superior).")
    cuerpo, variable, inferior, superior = nodo.args
    if not variable_ligable(variable):
        raise ValueError("Usa una letra minúscula libre, por ejemplo t, como variable de integración.")
    signo_inferior, signo_superior = signo_infinito(inferior), signo_infinito(superior)
    if signo_inferior and signo_inferior == signo_superior:
        raise ValueError("Los dos límites de integración no pueden ser el mismo infinito.")
    for limite in (inferior, superior):
        if not signo_infinito(limite):
            _validar_nodo(limite, profundidad + 1, variables)
    _validar_nodo(cuerpo, profundidad + 1, variables | {variable.id})


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
