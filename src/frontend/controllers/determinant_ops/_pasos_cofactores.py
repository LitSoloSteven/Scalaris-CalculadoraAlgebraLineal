"""Construcción de pasos, grupos y estadísticas para expansión por cofactores."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.backend.utils.formatters import format_fraction_str, number_to_latex


def _resumen_operaciones(cantidad: int) -> str:
    """Devuelve el texto de conteo de operaciones con el plural adecuado."""
    return "1 operación" if cantidad == 1 else f"{cantidad} operaciones"


def _construir_caso_1x1(
    resultado: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Genera el paso único, grupo y estadísticas cuando la matriz es 1×1."""
    det = Fraction(resultado.get("determinant", 0))
    det_str = format_fraction_str(det)
    det_tex = number_to_latex(det)
    pasos_raw = resultado.get("steps") or []
    latex_detalle = (
        pasos_raw[0].get("detail_latex")
        if pasos_raw
        else f"\\det(A) = {det_tex}"
    )

    paso = {
        "index": 0,
        "kind": "final",
        "description": f"Resultado: det(A) = {det_str}",
        "explanation": (
            f"En una matriz 1×1 el determinante es su único elemento: "
            f"det(A) = {det_str}."
        ),
        "group_index": 0,
        "matrix": None,
        "pivot": None,
        "rows_changed": [],
        "swap_rows": None,
        "detail_latex": latex_detalle,
        "menor": None,
    }
    grupo = {
        "title": "Resultado",
        "summary": "1 operación",
        "kind": "final",
        "step_indices": [0],
    }
    stats = {
        "total": 1,
        "pivotes": 0,
        "intercambios": 0,
        "eliminaciones": 0,
        "menores": 1,
        "terminos_cero": 1 if det == 0 else 0,
    }
    return [paso], [grupo], stats


def _armar_dict_menor(minor: dict[str, Any], col: int) -> dict[str, Any]:
    """Construye el diccionario detallado de un menor de la primera fila."""
    signo = int(minor.get("sign", 1))
    coef = Fraction(minor.get("coeff", 0))
    valor = Fraction(minor.get("value", 0))
    termino = Fraction(signo) * coef * valor

    signo_tex = "+1" if signo > 0 else "-1"
    coef_tex = number_to_latex(coef)
    valor_tex = number_to_latex(valor)
    termino_tex = number_to_latex(termino)

    return {
        "fila": 0,
        "columna": col,
        "signo": signo,
        "coeficiente_latex": coef_tex,
        "valor_latex": valor_tex,
        "coeficiente_str": format_fraction_str(coef),
        "valor_str": format_fraction_str(valor),
        "termino_latex": (
            f"({signo_tex}) \\cdot ({coef_tex}) \\cdot ({valor_tex}) = {termino_tex}"
        ),
        "expansion_latex": minor.get("expansion_latex"),
    }


def _construir_paso_menor(
    indice_paso: int,
    col: int,
    minor: dict[str, Any],
    paso_backend: dict[str, Any],
    matriz_a: Any,
) -> dict[str, Any]:
    """Construye el paso correspondiente al menor de la columna indicada."""
    datos_menor = _armar_dict_menor(minor, col)
    coef = Fraction(minor.get("coeff", 0))
    signo_simbolo = "+" if datos_menor["signo"] > 0 else "−"

    if coef == 0:
        explicacion = (
            f"Como el elemento a_1{col + 1} es 0, este término vale 0 sin "
            f"importar el valor del menor M_1{col + 1}."
        )
    else:
        explicacion = (
            f"Eliminamos la fila 1 y la columna {col + 1} para obtener "
            f"M_1{col + 1}. Con signo {signo_simbolo} y coeficiente "
            f"{datos_menor['coeficiente_str']}, calculamos su aporte."
        )

    return {
        "index": indice_paso,
        "kind": "menor",
        "description": (
            f"Menor M_1{col + 1} (signo {signo_simbolo}, "
            f"a_1{col + 1} = {datos_menor['coeficiente_str']})"
        ),
        "explanation": explicacion,
        "group_index": 1,
        "matrix": matriz_a,
        "pivot": None,
        "rows_changed": [0],
        "swap_rows": None,
        "detail_latex": paso_backend.get("detail_latex"),
        "menor": datos_menor,
    }


def _latex_suma_final(minors: list[dict[str, Any]], det: Fraction) -> str:
    """Formatea la suma algebraica de los términos evaluados igualada a det(A)."""
    partes: list[str] = []
    for idx, minor in enumerate(minors):
        termino = (
            Fraction(int(minor.get("sign", 1)))
            * Fraction(minor.get("coeff", 0))
            * Fraction(minor.get("value", 0))
        )
        if termino == 0:
            partes.append("0" if idx == 0 else "+ 0")
        elif idx == 0:
            partes.append(number_to_latex(termino))
        elif termino > 0:
            partes.append(f"+ {number_to_latex(termino)}")
        else:
            partes.append(f"- {number_to_latex(abs(termino))}")

    cuerpo = " ".join(partes) if partes else "0"
    return f"\\det(A) = {cuerpo} = {number_to_latex(det)}"


def construir_pasos_cofactores(
    resultado: dict[str, Any],
    n: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Transforma la salida de determinant_by_cofactors en pasos, grupos y stats."""
    if n == 1:
        return _construir_caso_1x1(resultado)

    pasos_raw = resultado.get("steps") or []
    minors = resultado.get("minors") or []
    det = Fraction(resultado.get("determinant", 0))
    det_str = format_fraction_str(det)
    matriz_a = pasos_raw[0].get("matrix") if pasos_raw else None

    pasos: list[dict[str, Any]] = [
        {
            "index": 0,
            "kind": "planteamiento",
            "description": "Expansión por cofactores de la fila 1",
            "explanation": (
                "Desarrollamos el determinante por la primera fila alternando "
                "los signos (+ − + …) y multiplicando cada entrada por su menor."
            ),
            "group_index": 0,
            "matrix": matriz_a,
            "pivot": None,
            "rows_changed": [0],
            "swap_rows": None,
            "detail_latex": pasos_raw[0].get("detail_latex") if pasos_raw else None,
            "menor": None,
        }
    ]

    indices_menores: list[int] = []
    terminos_cero = 0
    for j, minor in enumerate(minors):
        if Fraction(minor.get("coeff", 0)) == 0:
            terminos_cero += 1
        paso_b = pasos_raw[j + 1] if (j + 1) < len(pasos_raw) else {}
        idx = len(pasos)
        indices_menores.append(idx)
        pasos.append(_construir_paso_menor(idx, j, minor, paso_b, matriz_a))

    idx_final = len(pasos)
    pasos.append({
        "index": idx_final,
        "kind": "final",
        "description": f"Suma de cofactores: det(A) = {det_str}",
        "explanation": (
            f"Sumamos los aportes con signo de cada columna de la primera "
            f"fila y obtenemos det(A) = {det_str}."
        ),
        "group_index": 2,
        "matrix": None,
        "pivot": None,
        "rows_changed": [],
        "swap_rows": None,
        "detail_latex": _latex_suma_final(minors, det),
        "menor": None,
    })

    grupos = [
        {"title": "Planteamiento", "summary": "1 operación", "kind": "planteamiento", "step_indices": [0]},
        {"title": "Menores de la fila 1", "summary": _resumen_operaciones(len(indices_menores)), "kind": "menor", "step_indices": indices_menores},
        {"title": "Resultado", "summary": "1 operación", "kind": "final", "step_indices": [idx_final]},
    ]
    stats = {
        "total": len(pasos),
        "pivotes": 0,
        "intercambios": 0,
        "eliminaciones": 0,
        "menores": n,
        "terminos_cero": terminos_cero,
    }
    return pasos, grupos, stats