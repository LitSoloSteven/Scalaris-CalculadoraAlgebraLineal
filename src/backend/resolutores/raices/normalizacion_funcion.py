"""Normalización léxica acotada de notación matemática, sin ejecutar expresiones."""
import io
import re
import tokenize
from unicodedata import normalize

from .limites_biseccion import LONGITUD_MAXIMA_EXPRESION
from .notacion_calculo import AGREGADOS, POSTFIJOS, envolver_postfijo

_OPERADORES = {"+", "-", "*", "/", "**", "^", "(", ")", ","}
_OMITIDOS = {tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER}
_DIGITOS_SUPERIORES = "⁰¹²³⁴⁵⁶⁷⁸⁹"
_SUPERINDICES = str.maketrans(_DIGITOS_SUPERIORES + "⁺⁻", "0123456789+-")
_POTENCIA_TIPOGRAFICA = re.compile(rf"[⁺⁻]?[{_DIGITOS_SUPERIORES}]+")
_FRACCIONES = "¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞↉"
_SIMBOLOS = str.maketrans({
    "−": "-", "×": "*", "·": "*", "⋅": "*", "∙": "*",
    "÷": "/", "⁄": "/", "∕": "/", "√": " sqrt", "∛": " cbrt", "∜": " raiz4",
    "π": " pi ", "ℯ": " e ",
    **{simbolo: " " + nombre for simbolo, nombre in AGREGADOS.items()},
    **{fraccion: "(" + normalize("NFKC", fraccion).replace("⁄", "/") + ")" for fraccion in _FRACCIONES},
})


def normalizar_expresion(expresion: str) -> str:
    """Devuelve sintaxis explícita; lanza ValueError ante símbolos o longitud inválidos."""
    _comprobar_longitud(expresion)
    texto = expresion.translate(_SIMBOLOS).strip()
    texto = _POTENCIA_TIPOGRAFICA.sub(_explicitar_potencia, texto)
    _comprobar_longitud(texto)
    tokens = _obtener_tokens(texto)
    partes = []
    anterior = None
    for actual in tokens:
        if actual.string in POSTFIJOS:
            envolver_postfijo(partes, actual.string)
            anterior = actual._replace(type=tokenize.OP, string=")")
            continue
        if actual.string == ")" and anterior is not None and anterior.string == ",":
            raise ValueError("Escribe un argumento después de la última coma.")
        if anterior is not None and _requiere_producto(anterior, actual):
            partes.append("*")
        elif anterior is not None and _requiere_espacio(anterior, actual):
            partes.append(" ")
        partes.append("**" if actual.type == tokenize.OP and actual.string == "^" else actual.string)
        anterior = actual
    normalizada = "".join(partes)
    _comprobar_longitud(normalizada)
    return normalizada


def _explicitar_potencia(grupo: re.Match[str]) -> str:
    exponente = grupo[0].translate(_SUPERINDICES)
    resto = grupo.string[grupo.end():].lstrip()
    return f"**({exponente})" if resto[:1] in POSTFIJOS else "**" + exponente


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
    if token.type == tokenize.NEWLINE and token.string:
        raise ValueError("Escribe una sola expresión; usa paréntesis para continuarla en otra línea.")
    if token.type in _OMITIDOS:
        return False
    if token.type == tokenize.NUMBER:
        return True
    if token.type == tokenize.NAME and re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", token.string):
        return True
    if token.type == tokenize.OP and token.string in _OPERADORES:
        return True
    if token.type == tokenize.ERRORTOKEN and token.string in POSTFIJOS:
        return True
    if token.type == tokenize.ERRORTOKEN and token.string in (" ", "\t"):
        return False
    raise ValueError("La expresión contiene un símbolo u operación no permitidos.")


def _requiere_producto(anterior: tokenize.TokenInfo, actual: tokenize.TokenInfo) -> bool:
    termina_valor = anterior.type in (tokenize.NUMBER, tokenize.NAME) or anterior.string == ")"
    if actual.type == tokenize.NAME:
        return termina_valor
    if actual.string == "(":
        return anterior.type == tokenize.NUMBER or anterior.string == ")"
    return anterior.string == ")" and actual.type == tokenize.NUMBER


def _requiere_espacio(anterior: tokenize.TokenInfo, actual: tokenize.TokenInfo) -> bool:
    if actual.type == tokenize.NUMBER and anterior.type in (tokenize.NAME, tokenize.NUMBER):
        return True
    operadores = anterior.type == actual.type == tokenize.OP
    return operadores and anterior.string not in ("(", ")") and actual.string not in ("(", ")")
