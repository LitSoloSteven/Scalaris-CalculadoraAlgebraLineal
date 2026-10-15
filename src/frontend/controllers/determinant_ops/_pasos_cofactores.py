"""Construcción de pasos, grupos y estadísticas para expansión por cofactores."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.frontend.controllers.determinant_ops._pasos_comunes import (
    construir_caso_1x1,
    crear_paso,
    latex_suma_terminos,
    resumen_operaciones,
)

GRUPO_PLANTEAMIENTO = 0
GRUPO_MENORES = 1
GRUPO_RESULTADO = 2


def _caso_1x1(
    resultado: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Genera el paso único cuando la matriz es 1×1."""
    det = Fraction(resultado.get("determinant", 0))
    pasos_raw = resultado.get("steps") or []
    detalle = (
        pasos_raw[0].get("detail_latex")
        if pasos_raw
        else f"\\det(A) = {number_to_latex(det)}"
    )
    return construir_caso_1x1(
        resultado,
        matriz=None,
        detalle_latex=detalle,
        menores=1,
        terminos_cero=1 if det == 0 else 0,
    )


def _armar_dict_menor(minor: dict[str, Any], col: int) -> dict[str, Any]:
    """Construye el diccionario detallado de un menor de la primera fila."""
    signo = int(minor.get("sign", 1))
    coef = Fraction(minor.get("coeff", 0))
    valor = Fraction(minor.get("value", 0))
    termino = Fraction(signo) * coef * valor

    signo_tex = "+1" if signo > 0 else "-1"
    coef_tex = number_to_latex(coef)
    valor_tex = number_to_latex(valor)

    return {
        "fila": 0,
        "columna": col,
        "signo": signo,
        "coeficiente_latex": coef_tex,
        "valor_latex": valor_tex,
        "coeficiente_str": format_fraction_str(coef),
        "valor_str": format_fraction_str(valor),
        "termino_latex": (
            f"({signo_tex}) \\cdot ({coef_tex}) \\cdot ({valor_tex}) = {number_to_latex(termino)}"
        ),
        "expansion_latex": minor.get("expansion_latex"),
    }


def _explicacion_menor(col: int, coef: Fraction, datos: dict[str, Any], simbolo: str) -> str:
    """Redacta la explicación del aporte de un menor, con caso especial para coeficiente 0."""
    if coef == 0:
        return (
            f"Como el elemento a_1{col + 1} es 0, este término vale 0 sin "
            f"importar el valor del menor M_1{col + 1}."
        )
    return (
        f"Eliminamos la fila 1 y la columna {col + 1} para obtener "
        f"M_1{col + 1}. Con signo {simbolo} y coeficiente "
        f"{datos['coeficiente_str']}, calculamos su aporte."
    )


def _construir_paso_menor(
    indice_paso: int,
    col: int,
    minor: dict[str, Any],
    paso_backend: dict[str, Any],
    matriz_a: Any,
) -> dict[str, Any]:
    """Construye el paso correspondiente al menor de la columna indicada."""
    datos = _armar_dict_menor(minor, col)
    simbolo = "+" if datos["signo"] > 0 else "−"
    descripcion = (
        f"Menor M_1{col + 1} (signo {simbolo}, a_1{col + 1} = {datos['coeficiente_str']})"
    )
    explicacion = _explicacion_menor(col, Fraction(minor.get("coeff", 0)), datos, simbolo)
    return crear_paso(
        indice_paso,
        "menor",
        GRUPO_MENORES,
        (descripcion, explicacion),
        matrix=matriz_a,
        rows_changed=[0],
        detail_latex=paso_backend.get("detail_latex"),
        menor=datos,
    )


def _paso_planteamiento(pasos_raw: list[dict[str, Any]], matriz_a: Any) -> dict[str, Any]:
    """Construye el paso inicial con la fórmula de la expansión por la primera fila."""
    textos = (
        "Expansión por cofactores de la fila 1",
        "Desarrollamos el determinante por la primera fila alternando "
        "los signos (+ − + …) y multiplicando cada entrada por su menor.",
    )
    detalle = pasos_raw[0].get("detail_latex") if pasos_raw else None
    return crear_paso(
        0, "planteamiento", GRUPO_PLANTEAMIENTO, textos,
        matrix=matriz_a, rows_changed=[0], detail_latex=detalle,
    )


def _paso_final(indice: int, menores: list[dict[str, Any]], det: Fraction) -> dict[str, Any]:
    """Construye el paso de cierre con la suma de los aportes de cada menor."""
    det_str = format_fraction_str(det)
    cuerpo, _ = latex_suma_terminos(menores)
    textos = (
        f"Suma de cofactores: det(A) = {det_str}",
        f"Sumamos los aportes con signo de cada columna de la primera "
        f"fila y obtenemos det(A) = {det_str}.",
    )
    return crear_paso(
        indice, "final", GRUPO_RESULTADO, textos,
        detail_latex=f"\\det(A) = {cuerpo} = {number_to_latex(det)}",
    )


def _grupos(indices_menores: list[int], indice_final: int) -> list[dict[str, Any]]:
    """Agrupa los pasos en planteamiento, menores y resultado."""
    return [
        {"title": "Planteamiento", "summary": resumen_operaciones(1), "kind": "planteamiento", "step_indices": [0]},
        {"title": "Menores de la fila 1", "summary": resumen_operaciones(len(indices_menores)), "kind": "menor", "step_indices": indices_menores},
        {"title": "Resultado", "summary": resumen_operaciones(1), "kind": "final", "step_indices": [indice_final]},
    ]


def construir_pasos_cofactores(
    resultado: dict[str, Any],
    n: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Transforma la salida de determinant_by_cofactors en pasos, grupos y stats."""
    if n == 1:
        return _caso_1x1(resultado)

    pasos_raw = resultado.get("steps") or []
    menores = resultado.get("minors") or []
    det = Fraction(resultado.get("determinant", 0))
    matriz_a = pasos_raw[0].get("matrix") if pasos_raw else None

    pasos = [_paso_planteamiento(pasos_raw, matriz_a)]
    for j, menor in enumerate(menores):
        paso_backend = pasos_raw[j + 1] if (j + 1) < len(pasos_raw) else {}
        pasos.append(_construir_paso_menor(len(pasos), j, menor, paso_backend, matriz_a))
    indices_menores = list(range(1, len(pasos)))
    pasos.append(_paso_final(len(pasos), menores, det))

    stats = {
        "total": len(pasos),
        "pivotes": 0,
        "intercambios": 0,
        "eliminaciones": 0,
        "menores": n,
        "terminos_cero": sum(1 for m in menores if Fraction(m.get("coeff", 0)) == 0),
    }
    return pasos, _grupos(indices_menores, len(pasos) - 1), stats