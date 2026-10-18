"""Verificación aritmética exacta de soluciones para sistemas lineales."""

from fractions import Fraction
from typing import Any

from src.backend.utilidades.formateadores import (
    formatear_fraccion_texto,
    numero_a_latex,
)


def _a_fraccion_estricta(valor: Any) -> tuple[bool, Fraction, str]:
    """Convierte a fracción exacta reutilizando la validación centralizada."""
    from src.backend.utilidades.validadores import ValidadorMatriz

    return ValidadorMatriz.parsear_numero_exacto(valor)


def _preparsear_entradas_verificacion(
    matriz_coeficientes: list[list[Any]],
    vector_solucion: list[Any],
    vector_independientes: list[Any],
) -> tuple[bool, list[list[Fraction]], list[Fraction], list[Fraction], list[str]]:
    """Convierte matrices y vectores a fracciones exactas previo al cálculo."""
    A_frac: list[list[Fraction]] = []
    for i, fila in enumerate(matriz_coeficientes):
        fila_frac: list[Fraction] = []
        for j, celda in enumerate(fila):
            correcto, frac, error = _a_fraccion_estricta(celda)
            if not correcto:
                return False, [], [], [], [f"Error en A[{i + 1},{j + 1}]: {error}"]
            fila_frac.append(frac)
        A_frac.append(fila_frac)

    x_frac: list[Fraction] = []
    for j, celda in enumerate(vector_solucion):
        correcto, frac, error = _a_fraccion_estricta(celda)
        if not correcto:
            return False, [], [], [], [f"Error en x[{j + 1}]: {error}"]
        x_frac.append(frac)

    b_frac: list[Fraction] = []
    for i, celda in enumerate(vector_independientes):
        correcto, frac, error = _a_fraccion_estricta(celda)
        if not correcto:
            return False, [], [], [], [f"Error en b[{i + 1}]: {error}"]
        b_frac.append(frac)

    return True, A_frac, x_frac, b_frac, []


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
    correcto, A_frac, x_frac, b_frac, reporte_error = _preparsear_entradas_verificacion(matriz_coeficientes, vector_solucion, vector_independientes)
    if not correcto:
        return False, reporte_error

    es_valida_total = True
    reporte = []

    for i in range(len(A_frac)):
        lado_izquierdo = Fraction(0)
        terminos = []
        for j in range(len(x_frac)):
            coef = A_frac[i][j]
            variable = x_frac[j]
            lado_izquierdo += coef * variable
            if como_latex:
                terminos.append(
                    rf"\left({numero_a_latex(coef)}\right) \cdot \left({numero_a_latex(variable)}\right)"
                )
            else:
                terminos.append(f"({formatear_fraccion_texto(coef)})·({formatear_fraccion_texto(variable)})")

        lado_derecho = b_frac[i]
        eq_correcta = (lado_izquierdo == lado_derecho)
        reporte.append(
            _formatear_renglon_verificacion(i, terminos, lado_izquierdo, lado_derecho, como_latex)
        )
        if not eq_correcta:
            es_valida_total = False

    return es_valida_total, reporte
