"""Verificación aritmética exacta de soluciones para sistemas lineales."""

from fractions import Fraction
from typing import Any
from src.backend.modelos.entrada_numerica import convertir_numero_exacto

from src.backend.utilidades.formateadores import (
    formatear_fraccion_texto,
    numero_a_latex,
)


def _preparsear_entradas_verificacion(
    matriz_coeficientes: list[list[Any]],
    vector_solucion: list[Any],
    vector_independientes: list[Any],
) -> tuple[bool, list[list[Fraction]], list[Fraction], list[Fraction], list[str]]:
    """Convierte matrices y vectores a fracciones exactas previo al cálculo."""
    coeficientes_exactos: list[list[Fraction]] = []
    for i, fila in enumerate(matriz_coeficientes):
        fila_exacta: list[Fraction] = []
        for j, celda in enumerate(fila):
            correcto, fraccion, error = convertir_numero_exacto(celda)
            if not correcto:
                return False, [], [], [], [f"Error en A[{i + 1},{j + 1}]: {error}"]
            fila_exacta.append(fraccion)
        coeficientes_exactos.append(fila_exacta)

    solucion_exacta: list[Fraction] = []
    for j, celda in enumerate(vector_solucion):
        correcto, fraccion, error = convertir_numero_exacto(celda)
        if not correcto:
            return False, [], [], [], [f"Error en x[{j + 1}]: {error}"]
        solucion_exacta.append(fraccion)

    independientes_exactos: list[Fraction] = []
    for i, celda in enumerate(vector_independientes):
        correcto, fraccion, error = convertir_numero_exacto(celda)
        if not correcto:
            return False, [], [], [], [f"Error en b[{i + 1}]: {error}"]
        independientes_exactos.append(fraccion)

    return True, coeficientes_exactos, solucion_exacta, independientes_exactos, []


def _formatear_renglon_verificacion(
    i: int,
    terminos: list[str],
    lado_izquierdo: Fraction,
    lado_derecho: Fraction,
    como_latex: bool,
) -> str:
    """Genera la cadena de reporte para un renglón de la verificación."""
    sustitucion = " + ".join(terminos)
    es_valida = (lado_izquierdo == lado_derecho)
    if como_latex:
        estado = "Correcto" if es_valida else "Incorrecto"
        return (
            rf"\text{{Ecuación {i + 1}: }} {sustitucion} = {numero_a_latex(lado_izquierdo)} \quad "
            rf"(\text{{{estado}}}, \; b_{{{i + 1}}} = {numero_a_latex(lado_derecho)})"
        )
    estado_texto = "Correcto" if es_valida else "Incorrecto"
    return (
        f"Ecuación {i + 1}: {sustitucion} = {formatear_fraccion_texto(lado_izquierdo)}  "
        f"{estado_texto} (b_{i + 1} = {formatear_fraccion_texto(lado_derecho)})"
    )


def verificar_solucion(
    matriz_coeficientes: list[list[Any]],
    vector_solucion: list[Any],
    vector_independientes: list[Any],
    como_latex: bool = False,
) -> tuple[bool, list[str]]:
    """Verifica si el vector x satisface el sistema Ax = b con precisión exacta."""
    correcto, coeficientes, solucion, independientes, reporte_error = _preparsear_entradas_verificacion(matriz_coeficientes, vector_solucion, vector_independientes)
    if not correcto:
        return False, reporte_error

    es_valida_total = True
    reporte = []

    for i in range(len(coeficientes)):
        lado_izquierdo = Fraction(0)
        terminos = []
        for j in range(len(solucion)):
            coeficiente = coeficientes[i][j]
            variable = solucion[j]
            lado_izquierdo += coeficiente * variable
            if como_latex:
                terminos.append(
                    rf"\left({numero_a_latex(coeficiente)}\right) \cdot \left({numero_a_latex(variable)}\right)"
                )
            else:
                terminos.append(f"({formatear_fraccion_texto(coeficiente)})·({formatear_fraccion_texto(variable)})")

        lado_derecho = independientes[i]
        igualdad_correcta = (lado_izquierdo == lado_derecho)
        reporte.append(
            _formatear_renglon_verificacion(i, terminos, lado_izquierdo, lado_derecho, como_latex)
        )
        if not igualdad_correcta:
            es_valida_total = False

    return es_valida_total, reporte
