"""Formateadores LaTeX específicos para el dominio vectorial."""

from fractions import Fraction
import re

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex


def vector_a_latex(vector: Matriz) -> str:
    """Renderiza un vector como matriz LaTeX bmatrix."""
    if vector.filas == 1 and vector.columnas > 1:
        columnas = [numero_a_latex(vector.obtener(0, j)) for j in range(vector.columnas)]
        return r"\begin{bmatrix} " + r" & ".join(columnas) + r" \end{bmatrix}"
    filas = [numero_a_latex(vector.obtener(i, 0)) for i in range(vector.filas)]
    return r"\begin{bmatrix} " + r" \\ ".join(filas) + r" \end{bmatrix}"


def matriz_aumentada_gauss_a_latex(matriz: Matriz, numero_variables: int | None = None) -> str:
    """Renderiza una matriz aumentada con barra divisoria vertical."""
    conteo_variables = (matriz.columnas - 1) if numero_variables is None else numero_variables
    espec_columnas = ("c" * conteo_variables) + "|c"
    filas = []
    for i in range(matriz.filas):
        valores_fila = [numero_a_latex(matriz.obtener(i, j)) for j in range(matriz.columnas)]
        filas.append(" & ".join(valores_fila))
    cuerpo = " \\\\ ".join(filas)
    return rf"\left[ \begin{{array}}{{{espec_columnas}}} {cuerpo} \end{{array}} \right]"


def formatear_variable_latex(nombre_variable: str) -> str:
    """Normaliza el nombre de una variable a modo matemático LaTeX."""
    if nombre_variable.startswith("\\"):
        return nombre_variable
    coincidencia = re.match(r"^([a-zA-Z]+)_?(\d+)$", nombre_variable)
    if coincidencia:
        letras, digitos = coincidencia.groups()
        return f"{letras}_{{{digitos}}}"
    return nombre_variable


def formatear_vector_latex(nombre_vector: str) -> str:
    """Formatea el símbolo de un vector en negrita canónica LaTeX."""
    if nombre_vector.startswith(r"\mathbf{"):
        return nombre_vector
    coincidencia = re.match(r"^([a-zA-Z]+)_?(\d+)$", nombre_vector)
    if coincidencia:
        letras, digitos = coincidencia.groups()
        if len(digitos) == 1:
            return rf"\mathbf{{{letras}}}_{digitos}"
        return rf"\mathbf{{{letras}}}_{{{digitos}}}"
    return rf"\mathbf{{{nombre_vector}}}"


def formatear_componente_escalar(valor: Fraction | int | float, variable: str) -> str:
    """Formatea la multiplicación de un escalar por una variable."""
    fraccion = Fraction(valor)
    if fraccion == 0:
        return "0"
    if fraccion == 1:
        return variable
    if fraccion == -1:
        return f"-{variable}"
    if fraccion.denominator == 1:
        return f"{fraccion.numerator} {variable}"
    return f"{numero_a_latex(fraccion)} {variable}"


def formatear_expresion_lineal(coeficientes: list[Fraction | int | float], variables: list[str]) -> str:
    """Combina los términos de una fila en una expresión lineal respetando signos."""
    partes = []
    for c_bruto, variable in zip(coeficientes, variables):
        coeficiente = Fraction(c_bruto)
        if coeficiente == 0:
            continue
        c_abs = abs(coeficiente)
        if c_abs == 1:
            termino = variable
        elif c_abs.denominator == 1:
            termino = f"{c_abs.numerator} {variable}"
        else:
            termino = f"{numero_a_latex(c_abs)} {variable}"

        _agregar_termino_con_signo(partes, termino, coeficiente)
    return " ".join(partes) if partes else "0"


def matriz_aumentada_a_latex(vectores: list[Matriz], objetivo: Matriz) -> str:
    """Renderiza la matriz aumentada [A | b] con línea divisoria."""
    numero_vectores = len(vectores)
    dimension = objetivo.filas
    espec_columnas = ("c" * numero_vectores) + "|c"
    filas = []
    for i in range(dimension):
        valores_fila = [numero_a_latex(vectores[j].obtener(i, 0)) for j in range(numero_vectores)]
        valores_fila.append(numero_a_latex(objetivo.obtener(i, 0)))
        filas.append(" & ".join(valores_fila))
    cuerpo = " \\\\ ".join(filas)
    return rf"\left[ \begin{{array}}{{{espec_columnas}}} {cuerpo} \end{{array}} \right]"


def formatear_combinacion_lineal_vector(
    coeficientes: list[Fraction | int | float], nombres_vector: list[str]
) -> str:
    """Formatea la combinación escalar-vector para la comprobación formal."""
    partes = []
    for c_bruto, v_nombre in zip(coeficientes, nombres_vector):
        coeficiente = Fraction(c_bruto)
        v_latex = formatear_vector_latex(v_nombre)
        if coeficiente == 0:
            continue
        c_abs = abs(coeficiente)
        if c_abs == 1:
            termino = v_latex
        elif c_abs.denominator == 1:
            termino = f"{c_abs.numerator}{v_latex}"
        else:
            termino = f"{numero_a_latex(c_abs)}{v_latex}"

        _agregar_termino_con_signo(partes, termino, coeficiente)
    return " ".join(partes) if partes else "0"


def _agregar_termino_con_signo(partes: list[str], termino: str, coeficiente: Fraction) -> None:
    if not partes:
        partes.append(f"-{termino}" if coeficiente < 0 else termino)
    else:
        signo = "-" if coeficiente < 0 else "+"
        partes.append(f"{signo} {termino}")
