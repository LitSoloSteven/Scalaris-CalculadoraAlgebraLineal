"""Normalización léxica acotada de notación matemática, sin ejecutar expresiones."""
import io
import re
import tokenize

from .limites_biseccion import LONGITUD_MAXIMA_EXPRESION

_OPERADORES = {"+", "-", "*", "/", "**", "^", "(", ")"}
_OMITIDOS = {tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER}
_SUPERINDICES = str.maketrans({"²": "2", "³": "3"})


def normalizar_expresion(expresion: str) -> str:
    """Devuelve sintaxis explícita; lanza ValueError ante símbolos o longitud inválidos."""
    _comprobar_longitud(expresion)
    texto = expresion.strip().replace("−", "-")
    texto = re.sub(r"[²³]+", lambda grupo: "**" + grupo[0].translate(_SUPERINDICES), texto)
    _comprobar_longitud(texto)
    tokens = _obtener_tokens(texto)
    partes = []
    anterior = None
    for actual in tokens:
        if anterior is not None and _requiere_producto(anterior, actual):
            partes.append("*")
        partes.append("**" if actual.type == tokenize.OP and actual.string == "^" else actual.string)
        anterior = actual
    normalizada = " ".join(partes)
    _comprobar_longitud(normalizada)
    return normalizada


def _comprobar_longitud(expresion: str) -> None:
    if not isinstance(expresion, str) or not expresion.strip():
        raise ValueError("La expresión f(x) es obligatoria.")
    if len(expresion) > LONGITUD_MAXIMA_EXPRESION:
        raise ValueError(f"La expresión excede {LONGITUD_MAXIMA_EXPRESION} caracteres.")


def _obtener_tokens(texto: str) -> list[tokenize.TokenInfo]:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(texto).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as error:
        raise ValueError("Sintaxis inválida. Revisa operadores, paréntesis y llamadas a funciones.") from error
    return [token for token in tokens if _token_admitido(token)]


def _token_admitido(token: tokenize.TokenInfo) -> bool:
    if token.type in _OMITIDOS:
        return False
    if token.type == tokenize.NUMBER:
        return True
    if token.type == tokenize.NAME and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", token.string):
        return True
    if token.type == tokenize.OP and token.string in _OPERADORES:
        return True
    raise ValueError("La expresión contiene un símbolo u operación no permitidos.")


def _requiere_producto(anterior: tokenize.TokenInfo, actual: tokenize.TokenInfo) -> bool:
    termina_valor = anterior.type in (tokenize.NUMBER, tokenize.NAME) or anterior.string == ")"
    if actual.type == tokenize.NAME:
        return termina_valor
    if actual.string == "(":
        return anterior.type == tokenize.NUMBER or anterior.string == ")"
    return anterior.string == ")" and actual.type == tokenize.NUMBER
