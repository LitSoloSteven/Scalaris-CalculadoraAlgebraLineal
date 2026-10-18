"""Analizador léxico y sintáctico para expresiones matriciales mediante RPN."""

import re


def tokenizar_expresion(expresion: str) -> list[str]:
    """Convierte la cadena en tokens e inserta multiplicaciones implícitas."""
    expresion_limpia = expresion.replace(" ", "").replace("^T", "ᵀ").replace("^t", "ᵀ")
    patron = re.compile(
        r"\d+\.\d+|\d+|[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*|[A-Za-z][0-9]+|[A-Za-z]|ᵀ|[\+\-\*\(\)]"
    )
    tokens_brutos = patron.findall(expresion_limpia)
    if "".join(tokens_brutos) != expresion_limpia:
        raise ValueError("La expresión contiene caracteres no soportados (p. ej. '/').")

    tokens = []
    for i, token in enumerate(tokens_brutos):
        if token == "-" and (i == 0 or tokens_brutos[i - 1] in ("(", "+", "-", "*")):
            tokens.append("¬")
            continue
        tokens.append(token)
        if i < len(tokens_brutos) - 1:
            siguiente = tokens_brutos[i + 1]
            es_actual = bool(re.match(r"^[A-Za-z]|\d|\)|ᵀ", token))
            es_siguiente = bool(re.match(r"^[A-Za-z]|\d|\(", siguiente))
            if es_actual and es_siguiente:
                tokens.append("*")
    return tokens


def _manejar_cierre_parentesis(pila: list[str], salida: list[str]) -> None:
    """Vacía la pila hasta encontrar el paréntesis de apertura correspondiente."""
    while pila and pila[-1] != "(":
        salida.append(pila.pop())
    if not pila:
        raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
    pila.pop()


def _manejar_operador(
    token: str, pila: list[str], salida: list[str], precedencia: dict[str, int]
) -> None:
    """Mueve operadores de mayor o igual precedencia a la salida y apila el actual."""
    while pila and pila[-1] != "(":
        precedencia_tope = precedencia.get(pila[-1], 0)
        precedencia_actual = precedencia[token]
        condicion = precedencia_tope > precedencia_actual or (precedencia_tope == precedencia_actual and token != "¬")
        if not condicion:
            break
        salida.append(pila.pop())
    pila.append(token)


def convertir_a_rpn(tokens: list[str]) -> list[str]:
    """Aplica Shunting-Yard para convertir tokens a Notación Polaca Inversa."""
    precedencia = {"+": 1, "-": 1, "*": 2, "ᵀ": 3, "¬": 4}
    salida, pila = [], []
    for token in tokens:
        if re.match(r"^[A-Za-z][A-Za-z0-9_]*$|^\d+(\.\d+)?$", token):
            salida.append(token)
            continue
        if token == "(":
            pila.append(token)
            continue
        if token == ")":
            _manejar_cierre_parentesis(pila, salida)
            continue
        if token in precedencia:
            _manejar_operador(token, pila, salida, precedencia)

    while pila:
        tope = pila.pop()
        if tope in "()":
            raise ValueError("Error de sintaxis: Paréntesis desbalanceados.")
        salida.append(tope)
    return salida
