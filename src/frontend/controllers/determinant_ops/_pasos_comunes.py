"""Piezas compartidas por los constructores de pasos de determinantes."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.backend.utils.formatters import format_fraction_str, number_to_latex

TIPO_FINAL = "final"


def resumen_operaciones(cantidad: int) -> str:
    """Devuelve el conteo de operaciones con el plural adecuado."""
    return "1 operación" if cantidad == 1 else f"{cantidad} operaciones"


def crear_paso(
    indice: int,
    tipo: str,
    indice_grupo: int,
    textos: tuple[str, str],
    **campos: Any,
) -> dict[str, Any]:
    """Crea un paso con todas las claves del contrato y aplica los campos opcionales.

    Args:
        indice: Posición del paso en la secuencia.
        tipo: Clave del tipo de paso.
        indice_grupo: Fase a la que pertenece.
        textos: Tupla (descripción, explicación).
        **campos: Valores que sustituyen los de por defecto (matrix, pivot, detail_latex, etc.).
    """
    descripcion, explicacion = textos
    paso: dict[str, Any] = {
        "index": indice,
        "kind": tipo,
        "description": descripcion,
        "explanation": explicacion,
        "group_index": indice_grupo,
        "matrix": None,
        "pivot": None,
        "rows_changed": [],
        "swap_rows": None,
        "detail_latex": None,
        "menor": None,
    }
    paso.update(campos)
    return paso


def construir_caso_1x1(
    resultado: dict[str, Any],
    *,
    matriz: Any,
    detalle_latex: str | None,
    menores: int,
    terminos_cero: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Genera el único paso, el grupo y las estadísticas de una matriz 1×1."""
    det = Fraction(resultado.get("determinant", 0))
    det_str = format_fraction_str(det)
    textos = (
        f"Resultado: det(A) = {det_str}",
        f"En una matriz 1×1 el determinante es su único elemento: det(A) = {det_str}.",
    )
    paso = crear_paso(0, TIPO_FINAL, 0, textos, matrix=matriz, detail_latex=detalle_latex)
    grupo = {
        "title": "Resultado",
        "summary": resumen_operaciones(1),
        "kind": TIPO_FINAL,
        "step_indices": [0],
    }
    stats = {
        "total": 1,
        "pivotes": 0,
        "intercambios": 0,
        "eliminaciones": 0,
        "menores": menores,
        "terminos_cero": terminos_cero,
    }
    return [paso], [grupo], stats


def _parte_latex(termino: Fraction, posicion: int) -> str:
    """Formatea un término de la suma con su signo según su posición."""
    if termino == 0:
        return "0" if posicion == 0 else "+ 0"
    if posicion == 0:
        return number_to_latex(termino)
    if termino > 0:
        return f"+ {number_to_latex(termino)}"
    return f"- {number_to_latex(abs(termino))}"


def latex_suma_terminos(menores: list[dict[str, Any]]) -> tuple[str, Fraction]:
    """Devuelve la suma de signo·coeficiente·menor en LaTeX y su valor exacto."""
    partes: list[str] = []
    suma = Fraction(0)
    for posicion, menor in enumerate(menores):
        termino = (
            Fraction(int(menor.get("sign", 1)))
            * Fraction(menor.get("coeff", 0))
            * Fraction(menor.get("value", 0))
        )
        suma += termino
        partes.append(_parte_latex(termino, posicion))
    return (" ".join(partes) if partes else "0"), suma