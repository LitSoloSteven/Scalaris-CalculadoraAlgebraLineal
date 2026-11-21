"""Vocabulario y normalización de operadores tipográficos de cálculo."""

import ast
import re

POSTFIJOS = {"°": "grados", "‰": "por_mil", "′": "derivada", "″": "derivada_segunda"}
AGREGADOS = {"∑": "sumatoria", "∏": "productoria"}
DERIVADAS = {POSTFIJOS["′"]: 1, POSTFIJOS["″"]: 2}
TRIGONOMETRICAS_DIRECTAS = ("sin", "cos", "tan")
TRIGONOMETRICAS_INVERSAS = ("asin", "acos", "atan")
ANGULARES_RADIANES = {
    nombre: nombre + "_radianes"
    for nombre in (*TRIGONOMETRICAS_DIRECTAS, *TRIGONOMETRICAS_INVERSAS)
}
NOMBRES_ANGULARES = {alias: nombre for nombre, alias in ANGULARES_RADIANES.items()}
GRADOS_POR_MEDIA_VUELTA = 180
UNIDADES_POR_MIL = 1000
MAXIMO_TERMINOS_AGREGADO = 32


def entero_literal(nodo: ast.AST) -> int:
    """Extrae un entero literal con signo opcional; lanza ValueError si es una expresión."""
    signo = -1 if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub) else 1
    if isinstance(nodo, ast.UnaryOp):
        nodo = nodo.operand
    if isinstance(nodo, ast.Constant) and type(nodo.value) is int:
        return signo * nodo.value
    raise ValueError("Usa límites enteros en la sumatoria o productoria.")


def envolver_postfijo(partes: list[str], simbolo: str) -> None:
    """Reemplaza el operando previo por una llamada; rechaza un postfijo sin operando."""
    inicio = _inicio_atomo(partes, len(partes) - 1)
    if simbolo in ("′", "″"):
        while inicio > 0 and partes[inicio - 1] == "**":
            inicio = _inicio_atomo(partes, inicio - 2)
    partes.insert(inicio, POSTFIJOS[simbolo] + "(")
    partes.append(")")


def _inicio_atomo(partes: list[str], fin: int) -> int:
    if fin < 0:
        raise ValueError("Escribe un valor antes del símbolo de cálculo.")
    if partes[fin] != ")":
        if re.match(r"[A-Za-z_0-9.]", partes[fin]):
            return fin
        raise ValueError("Escribe un valor antes del símbolo de cálculo.")
    nivel = 1
    for inicio in range(fin - 1, -1, -1):
        parte = partes[inicio]
        nivel += (parte == ")") - parte.endswith("(")
        if nivel == 0:
            return _incluir_nombre_llamada(partes, inicio)
    raise ValueError("Cierra los paréntesis antes del símbolo de cálculo.")


def _incluir_nombre_llamada(partes: list[str], inicio: int) -> int:
    anterior = partes[inicio - 1] if inicio else ""
    if partes[inicio] == "(" and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", anterior):
        return inicio - 1
    return inicio
