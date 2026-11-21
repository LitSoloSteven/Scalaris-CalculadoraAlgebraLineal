"""Vocabulario y normalización de operadores tipográficos de cálculo."""

import re

POSTFIJOS = {"°": "grados", "‰": "por_mil", "′": "derivada", "″": "derivada_segunda"}
AGREGADOS = {"∑": "sumatoria", "∏": "productoria"}
DERIVADAS = {POSTFIJOS["′"]: 1, POSTFIJOS["″"]: 2}


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
