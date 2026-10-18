"""Funciones de formateo textual y LaTeX para números y expresiones."""

from fractions import Fraction
import re
from typing import Dict

from src.backend.constantes import (
    CERO_EPSILON,
    DECIMALES_VISUALIZACION,
    LIMITE_DENOMINADOR_LATEX,
    LIMITE_VISUALIZACION_FRACCION,
    TOLERANCIA_COINCIDENCIA_FRACCION,
    TOLERANCIA_FRACCION_VISUALIZACION,
)


def formatear_variable_para_latex(nombre_variable: str) -> str:
    """Convierte el identificador de una variable a notación LaTeX con subíndice."""
    coincidencia = re.match(r"^([a-zA-Z]+)(\d+)$", nombre_variable)
    if coincidencia:
        letras, digitos = coincidencia.groups()
        return f"{letras}_{{{digitos}}}"
    if len(nombre_variable) > 1:
        return f"\\text{{{nombre_variable}}}"
    return nombre_variable


def formatear_fraccion_texto(valor: float | Fraction | int) -> str:
    """Formatea valores a cadenas fraccionarias exactas o decimales legibles."""
    if isinstance(valor, (int, Fraction)):
        fraccion = Fraction(valor)
        if fraccion.denominator == 1:
            return str(fraccion.numerator)
        return f"{fraccion.numerator}/{fraccion.denominator}"

    if isinstance(valor, float):
        if abs(valor) < CERO_EPSILON:
            return "0"
        frac = Fraction(valor).limit_denominator(LIMITE_VISUALIZACION_FRACCION)
        if abs(float(frac) - valor) < TOLERANCIA_FRACCION_VISUALIZACION:
            if frac.denominator == 1:
                return str(frac.numerator)
            return f"{frac.numerator}/{frac.denominator}"
        return f"{valor:.{DECIMALES_VISUALIZACION}f}".rstrip("0").rstrip(".")

    return str(valor)


def numero_a_latex(valor: float | Fraction | int) -> str:
    """Convierte un valor numérico a expresión fraccionaria formateada para LaTeX."""
    if isinstance(valor, (int, Fraction)):
        fraccion = Fraction(valor)
        if fraccion == 0:
            return "0"
        numero, den = fraccion.numerator, fraccion.denominator
        if den == 1:
            return str(numero)
        signo = "-" if numero < 0 else ""
        return f"{signo}\\frac{{{abs(numero)}}}{{{den}}}"

    if isinstance(valor, float):
        if abs(valor) < TOLERANCIA_COINCIDENCIA_FRACCION:
            return "0"
        frac = Fraction(valor).limit_denominator(LIMITE_DENOMINADOR_LATEX)
        if abs(float(frac) - valor) < TOLERANCIA_FRACCION_VISUALIZACION:
            numero, den = frac.numerator, frac.denominator
            if den == 1:
                return str(numero)
            signo = "-" if numero < 0 else ""
            return f"{signo}\\frac{{{abs(numero)}}}{{{den}}}"
        return f"{valor:.{DECIMALES_VISUALIZACION}f}".rstrip("0").rstrip(".")

    return str(valor)


def formatear_expresion_parametrica(
    constante: Fraction,
    terminos: Dict[str, Fraction],
) -> str:
    """Convierte constantes y términos lineales a una cadena paramétrica ordenada."""
    partes = []
    tiene_constante = (constante != 0) or not terminos

    if tiene_constante:
        partes.append(formatear_fraccion_texto(constante))

    for variable, coeficiente in terminos.items():
        if coeficiente == 0:
            continue
        coeficiente_texto = _formatear_coeficiente_parametrico(abs(coeficiente))

        if not partes:
            prefijo = "" if coeficiente > 0 else "-"
            partes.append(f"{prefijo}{coeficiente_texto}{variable}")
        else:
            signo = "+" if coeficiente > 0 else "-"
            partes.append(f"{signo} {coeficiente_texto}{variable}")

    return " ".join(partes) if partes else "0"


def _formatear_coeficiente_parametrico(coeficiente: Fraction) -> str:
    """Omite el coeficiente unitario y agrupa las fracciones entre paréntesis."""
    if coeficiente.denominator == 1:
        return "" if coeficiente.numerator == 1 else str(coeficiente.numerator)
    return f"({coeficiente.numerator}/{coeficiente.denominator})"
