"""Análisis léxico y conversión a notación polaca inversa de expresiones matriciales."""

import re

from src.backend.modelos.entrada_numerica import (
    DIVISIONES_TIPOGRAFICAS,
    FRACCIONES_TIPOGRAFICAS,
    SIGNO_MENOS_TIPOGRAFICO,
    SIMBOLO_POR_MIL,
)

OPERADORES_BINARIOS = {"+": 1, "-": 1, "⊕": 1, "*": 2, "/": 2, "⊗": 2}
_PRECEDENCIA = {**OPERADORES_BINARIOS, "¬": 3}
_DIGITOS_SUPERIORES = "⁰¹²³⁴⁵⁶⁷⁸⁹"
_DIGITOS_EXPONENTE = str.maketrans(_DIGITOS_SUPERIORES + "⁻", "0123456789-")
_TRADUCCION = str.maketrans(
    SIGNO_MENOS_TIPOGRAFICO + "×·⋅∙" + DIVISIONES_TIPOGRAFICAS, "-****///"
)
_NUMERO = rf"(?:[0-9]+(?:\.[0-9]+)?|[{FRACCIONES_TIPOGRAFICAS}]){SIMBOLO_POR_MIL}?"
_MATRIZ = r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*|[A-Za-z][0-9]+|[A-Za-z]"
_POTENCIA = rf"[⁻]?[{_DIGITOS_SUPERIORES}]+"
_PATRON = re.compile(rf"{_NUMERO}|{_MATRIZ}|{_POTENCIA}|ᵀ|[+*/⊕⊗()\-]")
_ERROR_SINTAXIS = "Expresión matemática mal formada."


def es_numero(token: str) -> bool:
    """Indica si el token representa un literal racional."""
    return re.fullmatch(_NUMERO, token) is not None


def es_nombre_matriz(token: str) -> bool:
    """Indica si el token identifica una matriz."""
    return re.fullmatch(_MATRIZ, token) is not None


def exponente_de(token: str) -> int | None:
    """Devuelve el entero del superíndice o None para los demás tokens."""
    if re.fullmatch(_POTENCIA, token):
        return int(token.translate(_DIGITOS_EXPONENTE))
    return None


def _es_postfijo(token: str) -> bool:
    return token == "ᵀ" or re.fullmatch(_POTENCIA, token) is not None


def _es_operando(token: str) -> bool:
    return es_numero(token) or es_nombre_matriz(token)


def tokenizar_expresion(expresion: str) -> list[str]:
    """Separa tokens e inserta productos implícitos. Rechaza caracteres ajenos a la gramática."""
    limpia = "".join(expresion.split()).translate(_TRADUCCION)
    limpia = limpia.replace("^T", "ᵀ").replace("^t", "ᵀ")
    brutos = _PATRON.findall(limpia)
    if "".join(brutos) != limpia:
        raise ValueError("La expresión contiene caracteres no soportados.")

    tokens = []
    espera_operando = True
    for token in brutos:
        if (_es_operando(token) or token == "(") and not espera_operando:
            tokens.append("*")
        if token == "-" and espera_operando:
            token = "¬"
        tokens.append(token)
        espera_operando = token in _PRECEDENCIA or token == "("
    return tokens


def _cerrar_parentesis(pila: list[str], salida: list[str]) -> None:
    while pila and pila[-1] != "(":
        salida.append(pila.pop())
    if not pila:
        raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
    pila.pop()


def _apilar_binario(token: str, pila: list[str], salida: list[str]) -> None:
    while pila and _PRECEDENCIA.get(pila[-1], 0) >= _PRECEDENCIA[token]:
        salida.append(pila.pop())
    pila.append(token)


def convertir_a_rpn(tokens: list[str]) -> list[str]:
    """Devuelve los tokens en orden de evaluación o lanza ValueError por sintaxis inválida."""
    salida, pila = [], []
    espera_operando = True
    for token in tokens:
        if espera_operando:
            if token in ("(", "¬"):
                pila.append(token)
                continue
            if not _es_operando(token):
                raise ValueError(_ERROR_SINTAXIS)
            salida.append(token)
            espera_operando = False
            continue
        if _es_postfijo(token):
            salida.append(token)
        elif token == ")":
            _cerrar_parentesis(pila, salida)
        elif token in OPERADORES_BINARIOS:
            _apilar_binario(token, pila, salida)
            espera_operando = True
        else:
            raise ValueError(_ERROR_SINTAXIS)

    if espera_operando:
        raise ValueError(_ERROR_SINTAXIS)
    while pila:
        tope = pila.pop()
        if tope == "(":
            raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
        salida.append(tope)
    return salida
