"""Funciones puras para generar la vista previa LaTeX del determinante."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.backend.utils.validators import MatrixValidator
from src.backend.utils.formatters import number_to_latex


def _sanitizar_celda_previa(val: Any) -> str:
    """Convierte el texto de una celda en LaTeX seguro para la vista previa."""
    if val is None or str(val).strip() == "":
        return "0"
    texto = str(val).strip()
    exito, fraccion, _ = MatrixValidator.parse_number_exact(texto)
    if not exito:
        return r"\color{gray}{?}"
    return number_to_latex(fraccion)


def contar_invalidas(datos: list[list[str]]) -> int:
    """Cuenta cuántas celdas de la cuadrícula no son números o fracciones válidas."""
    if not isinstance(datos, list) or not datos:
        return 0
    invalidas = 0
    for fila in datos:
        if not isinstance(fila, list):
            continue
        for celda in fila:
            texto = str(celda).strip() if celda is not None else ""
            if texto == "" or texto == "0":
                continue
            exito, _, _ = MatrixValidator.parse_number_exact(texto)
            if not exito:
                invalidas += 1
    return invalidas


def latex_vista_previa(datos: list[list[str]]) -> str:
    """Genera la cadena LaTeX para la matriz envuelta en vmatrix."""
    if not isinstance(datos, list) or not datos:
        return ""
    n = len(datos)
    filas_latex: list[str] = []
    for fila in datos:
        if not isinstance(fila, list) or len(fila) != n:
            return ""
        elementos = [_sanitizar_celda_previa(celda) for celda in fila]
        filas_latex.append(" & ".join(elementos))

    cuerpo = " \\\\ ".join(filas_latex)
    return rf"\det(A) = \begin{{vmatrix}} {cuerpo} \end{{vmatrix}}"