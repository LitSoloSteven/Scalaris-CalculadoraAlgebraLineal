"""Construcción de pasos y grupos didácticos para el reproductor en Sistemas Lineales."""

from __future__ import annotations

import re

from src.backend.models.matrix import Matrix
from src.frontend.componentes.reproductor_pasos.cuerpos import render_latex
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.helpers import formatear_paso_mathjax


class _CuerpoLatex:
    """Cuerpo ejecutable que renderiza la expresión LaTeX mediante render_latex."""

    def __init__(self, latex: str) -> None:
        self.latex = latex

    def __call__(self) -> None:
        render_latex(self.latex)

    def __str__(self) -> str:
        return self.latex


def _limpiar_latex_plano(texto: str) -> str:
    """Elimina etiquetas y comandos LaTeX comunes para dejar una descripción corta en texto plano."""
    t = re.sub(r"\\text\{([^}]*)\}", r"\1", str(texto))
    t = t.replace(r"\implies", "=>").replace(r"\;", " ").replace(r"\\", " ")
    t = re.sub(r"[{}\\]", "", t)
    return " ".join(t.split())


def _crear_paso_eliminacion(
    s: dict,
    steps_meta: list[dict],
    total_pasos: int,
    variables: list[str],
    n_vars: int,
) -> PasoReproductor:
    """Crea una instancia de PasoReproductor para un paso de eliminación gaussiana."""
    idx = s["index"]
    mat_dict = s.get("matrix", {})
    mat = Matrix(mat_dict["rows"], mat_dict["cols"], mat_dict["data"])
    pivote = tuple(s["pivot"]) if s.get("pivot") is not None else None
    cuerpo = html_tabla_aumentada(
        mat,
        n_vars,
        filas_cambiadas=tuple(s.get("rows_changed") or ()),
        pivote=pivote,
        filas_intercambio=tuple(s["swap_rows"]) if s.get("swap_rows") is not None else (),
        bloque_resultado=False,
        etiquetas_izq=variables,
        etiquetas_der=["b"],
    )
    meta = steps_meta[idx] if idx < len(steps_meta) else {
        "index": idx + 1, "total": total_pasos, "kind": s.get("kind", "otro"),
        "op": s.get("description", ""), "pivot": pivote,
        "rows_before": {}, "rows_after": {}, "cols": None,
    }
    return PasoReproductor(
        indice=idx, tipo=s.get("kind", "otro"),
        descripcion=s.get("description", ""),
        explicacion=s.get("explanation", ""),
        indice_grupo=s.get("group_index", 0),
        cuerpo=cuerpo, meta_explicar=meta,
    )


def _construir_pasos_eliminacion(
    steps_view: list[dict],
    groups_view: list[dict],
    steps_meta: list[dict],
    total_pasos: int,
    variables: list[str],
    n_vars: int,
) -> tuple[list[PasoReproductor], list[GrupoReproductor]]:
    """Genera pasos y grupos para las etapas de eliminación (matrices aumentadas)."""
    pasos = [
        _crear_paso_eliminacion(s, steps_meta, total_pasos, variables, n_vars)
        for s in steps_view
    ]
    grupos = [
        GrupoReproductor(
            titulo=g.get("title", ""), resumen=g.get("summary", ""),
            tipo=g.get("kind", "columna"), indices_pasos=tuple(g.get("step_indices", ())),
        )
        for g in groups_view
    ]
    return pasos, grupos


def _construir_pasos_sustitucion(
    back_steps: list[str],
    total_pasos: int,
    es_gauss_jordan: bool,
    inicio_paso: int,
    inicio_grupo: int,
) -> tuple[list[PasoReproductor], GrupoReproductor]:
    """Genera pasos y grupo de sustitución hacia atrás o lectura de solución."""
    pasos: list[PasoReproductor] = []
    indices: list[int] = []
    titulo = "Solución final" if es_gauss_jordan else "Sustitución hacia atrás"
    expl = (
        "Lectura del valor de la variable a partir de la forma escalonada reducida."
        if es_gauss_jordan
        else "Despejamos y sustituimos hacia atrás los valores conocidos para hallar la incógnita."
    )

    for i, linea in enumerate(back_steps):
        curr_idx = inicio_paso + i
        indices.append(curr_idx)
        op_texto = _limpiar_latex_plano(linea)
        meta = {
            "index": curr_idx + 1, "total": total_pasos, "kind": "sustitucion",
            "op": op_texto, "rows_before": {}, "rows_after": {}, "cols": None,
        }
        pasos.append(
            PasoReproductor(
                indice=curr_idx, tipo="sustitucion", descripcion=op_texto,
                explicacion=expl, indice_grupo=inicio_grupo,
                cuerpo=_CuerpoLatex(formatear_paso_mathjax(linea)), meta_explicar=meta,
            )
        )

    resumen = "1 operación" if len(indices) == 1 else f"{len(indices)} operaciones"
    grupo = GrupoReproductor(
        titulo=titulo, resumen=resumen, tipo="sustitucion", indices_pasos=tuple(indices)
    )
    return pasos, grupo


def _construir_pasos_verificacion(
    verif_steps: list[str],
    total_pasos: int,
    inicio_paso: int,
    inicio_grupo: int,
) -> tuple[list[PasoReproductor], GrupoReproductor]:
    """Genera pasos y grupo de comprobación Ax = b."""
    pasos: list[PasoReproductor] = []
    indices: list[int] = []
    expl = "Sustituimos la solución en la ecuación original para verificar que se cumple la igualdad."

    for i, linea in enumerate(verif_steps):
        curr_idx = inicio_paso + i
        indices.append(curr_idx)
        op_texto = _limpiar_latex_plano(linea)
        meta = {
            "index": curr_idx + 1, "total": total_pasos, "kind": "verificacion",
            "op": op_texto, "rows_before": {}, "rows_after": {}, "cols": None,
        }
        pasos.append(
            PasoReproductor(
                indice=curr_idx, tipo="verificacion", descripcion=op_texto,
                explicacion=expl, indice_grupo=inicio_grupo,
                cuerpo=_CuerpoLatex(formatear_paso_mathjax(linea)), meta_explicar=meta,
            )
        )

    resumen = "1 operación" if len(indices) == 1 else f"{len(indices)} operaciones"
    grupo = GrupoReproductor(
        titulo="Comprobación Ax = b", resumen=resumen, tipo="verificacion", indices_pasos=tuple(indices)
    )
    return pasos, grupo


def construir_pasos_reproductor(
    respuesta: dict,
    metodo: str | None = None,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye las tuplas de pasos y grupos del reproductor a partir de la respuesta del solver."""
    steps_view = respuesta.get("steps_view", [])
    if not steps_view:
        return (), ()

    back_steps = respuesta.get("back_substitution_steps") or []
    verif_steps = respuesta.get("verification_steps_latex") or []
    variables = respuesta.get("variables")
    n_vars = respuesta.get("n_vars", len(variables) if variables else 0)
    if not variables and n_vars > 0:
        variables = [f"x{i+1}" for i in range(n_vars)]

    total_pasos = len(steps_view) + len(back_steps) + len(verif_steps)
    pasos, grupos = _construir_pasos_eliminacion(
        steps_view, respuesta.get("groups", []), respuesta.get("steps_meta", []),
        total_pasos, variables, n_vars,
    )

    es_gauss_jordan = str(metodo).lower() in ("gauss-jordan", "gauss_jordan")
    if back_steps:
        p_sust, g_sust = _construir_pasos_sustitucion(
            back_steps, total_pasos, es_gauss_jordan, len(pasos), len(grupos)
        )
        pasos.extend(p_sust)
        grupos.append(g_sust)

    if verif_steps:
        p_verif, g_verif = _construir_pasos_verificacion(
            verif_steps, total_pasos, len(pasos), len(grupos)
        )
        pasos.extend(p_verif)
        grupos.append(g_verif)

    return tuple(pasos), tuple(grupos)
