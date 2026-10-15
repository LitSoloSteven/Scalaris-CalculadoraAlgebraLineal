"""Construcción de pasos, grupos y estadísticas para determinante por eliminación (LU)."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.backend.utils.formatters import format_fraction_str
from src.frontend.controllers._agrupar_pasos import agrupar_pasos_eliminacion
from src.frontend.controllers.determinant_ops._pasos_comunes import (
    construir_caso_1x1,
    crear_paso,
    resumen_operaciones,
)


def _caso_1x1(
    resultado: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Genera el único paso cuando la matriz de entrada es 1×1."""
    pasos_raw = resultado.get("steps") or []
    paso_cero = pasos_raw[0] if pasos_raw else {}
    return construir_caso_1x1(
        resultado,
        matriz=paso_cero.get("matrix"),
        detalle_latex=paso_cero.get("detail_latex"),
        menores=0,
        terminos_cero=0,
    )


def _explicar_paso_lu(paso: dict[str, Any], intercambios_acumulados: int) -> str:
    """Redacta la explicación pedagógica centrada en las propiedades del determinante."""
    kind = paso.get("kind", "")
    desc = paso.get("description", "")

    if kind == "inicial":
        return (
            "Llevamos la matriz A a forma triangular superior mediante operaciones "
            "elementales de fila para calcular el determinante con la diagonal."
        )
    if kind == "intercambio":
        signo = "−1" if intercambios_acumulados % 2 == 1 else "+1"
        return (
            f"Intercambiar dos filas invierte el signo del determinante. "
            f"Llevas {intercambios_acumulados} intercambio(s), por lo que el factor "
            f"de signo acumulado es (−1)^{intercambios_acumulados} = {signo}."
        )
    if kind == "pivote":
        pivote = paso.get("pivot")
        mat = paso.get("matrix")
        if pivote and mat is not None:
            fila_p, col_p = pivote[0], pivote[1]
            val_str = format_fraction_str(mat.get(fila_p, col_p))
            return (
                f"Seleccionamos el pivote en la fila {fila_p + 1}, columna {col_p + 1} "
                f"(valor {val_str}). Este valor multiplicará en el producto final de la diagonal."
            )
        return "Seleccionamos el pivote de la columna actual; su valor entrará en el producto de la diagonal."

    if kind == "eliminacion":
        return (
            f"{desc}. Sumar un múltiplo de una fila a otra fila mantiene "
            f"exactamente igual el valor del determinante."
        )
    return desc


def _postprocesar_pasos_base(
    pasos: list[dict[str, Any]],
    grupos: list[dict[str, Any]],
    pasos_raw: list[dict[str, Any]],
) -> None:
    """Ajusta títulos, descripciones, explicaciones y claves de los pasos agrupados."""
    for grupo in grupos:
        if grupo.get("kind") == "inicial":
            grupo["title"] = "Matriz inicial A"

    intercambios = 0
    for idx, paso in enumerate(pasos):
        if paso.get("kind") == "inicial":
            paso["description"] = "Matriz inicial A"
        elif paso.get("kind") == "intercambio":
            intercambios += 1

        paso["explanation"] = _explicar_paso_lu(paso, intercambios)
        paso["detail_latex"] = (
            pasos_raw[idx].get("detail_latex")
            if idx < len(pasos_raw)
            else paso.get("detail_latex")
        )
        paso["menor"] = None
        paso.setdefault("pivot", None)
        paso.setdefault("rows_changed", [])
        paso.setdefault("swap_rows", None)


def _textos_cierre(det: Fraction, intercambios: int) -> tuple[str, str, str, str]:
    """Devuelve tipo, título de grupo, descripción y explicación del paso de cierre."""
    if det == 0:
        return (
            "singular",
            "Matriz singular",
            "Diagonal con pivote cero: det(A) = 0",
            "Al menos una columna quedó sin pivote no nulo, lo que deja un cero "
            "en la diagonal de U. El determinante es 0 y la matriz A no tiene inversa.",
        )
    det_str = format_fraction_str(det)
    factor_signo = "−1" if intercambios % 2 == 1 else "+1"
    return (
        "producto",
        "Producto de la diagonal",
        f"Producto de la diagonal: det(A) = {det_str}",
        f"Multiplicamos los pivotes de la diagonal principal de U y aplicamos "
        f"el signo (−1)^{intercambios} = {factor_signo} por los intercambios de fila: "
        f"det(A) = {det_str}.",
    )


def _construir_paso_cierre(
    resultado: dict[str, Any],
    paso_final_raw: dict[str, Any],
    ultima_matriz: Any,
    indice_paso: int,
    indice_grupo: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Crea el paso y grupo final (producto de la diagonal o detección de singularidad)."""
    det = Fraction(resultado.get("determinant", 0))
    tipo, titulo_grupo, descripcion, explicacion = _textos_cierre(
        det, int(resultado.get("swap_count", 0))
    )
    paso = crear_paso(
        indice_paso, tipo, indice_grupo, (descripcion, explicacion),
        matrix=ultima_matriz, detail_latex=paso_final_raw.get("detail_latex"),
    )
    grupo = {
        "title": titulo_grupo,
        "summary": resumen_operaciones(1),
        "kind": tipo,
        "step_indices": [indice_paso],
    }
    return paso, grupo


def construir_pasos_lu(
    resultado: dict[str, Any],
    n: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Construye pasos, grupos y estadísticas para determinant_by_lu."""
    if n == 1:
        return _caso_1x1(resultado)

    pasos_raw = resultado.get("steps") or []
    pasos_gauss_raw = pasos_raw[:-1] if len(pasos_raw) > 1 else []
    paso_cierre_raw = pasos_raw[-1] if pasos_raw else {}

    pasos, grupos, stats_base = agrupar_pasos_eliminacion(
        pasos_gauss_raw,
        n_izq=n,
        estado=None,
        contexto="sistema",
        metodo="gauss",
    )
    pasos = [dict(p) for p in pasos]
    grupos = [dict(g) for g in grupos]

    _postprocesar_pasos_base(pasos, grupos, pasos_gauss_raw)

    ultima_matriz = pasos[-1].get("matrix") if pasos else None
    paso_final, grupo_final = _construir_paso_cierre(
        resultado, paso_cierre_raw, ultima_matriz, len(pasos), len(grupos)
    )
    pasos.append(paso_final)
    grupos.append(grupo_final)

    stats = dict(stats_base)
    stats["total"] = len(pasos)
    stats["menores"] = 0
    stats["terminos_cero"] = 0
    return pasos, grupos, stats