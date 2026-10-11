"""Adaptador puro de segment_steps al modelo del reproductor de pasos en Matrices."""

from __future__ import annotations

import re

from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.controladores.operaciones_matrices import (
    ControladorOperacionesMatrices,
)


def limpiar_descripcion_operacion(op_display: str | None, default: str) -> str:
    """Genera una versión legible y en texto plano de operation_display."""
    if not op_display:
        return default
    t = re.sub(r"_\{(\w+)\}", r"\1", str(op_display))
    t = t.replace(r"\cdot", "·").replace("{", "").replace("}", "").strip()
    return " ".join(t.split())


def obtener_explicacion_operacion(tipo_op: str | None) -> str:
    """Devuelve una explicación concisa en español y tuteo según el tipo de operación."""
    t = (tipo_op or "").lower()
    if "suma" in t:
        return "Sumamos las matrices celda a celda."
    if "resta" in t:
        return "Restamos las matrices celda a celda."
    if "escalar" in t:
        return "Multiplicamos cada celda por el escalar."
    if "producto" in t or "multiplicaci" in t:
        return "Cada celda es el producto de una fila de A por una columna de B."
    if "transposi" in t:
        return "Las filas pasan a ser columnas."
    if "negaci" in t:
        return "Cambiamos el signo de cada celda."
    return "Aplicamos la operación celda a celda."


def _crear_paso_matriz(
    i: int, step: dict, total: int, varias_suboperaciones: bool
) -> PasoReproductor:
    """Crea un paso del reproductor a partir del segmento de cálculo matricial."""
    op_type = step.get("operation_type") or "Operación"
    op_disp = step.get("operation_display")
    desc = limpiar_descripcion_operacion(op_disp, f"Operación {i + 1}")
    expl = obtener_explicacion_operacion(op_type)
    meta = ControladorOperacionesMatrices.construir_foco_paso(step, i + 1, total)
    grupo_idx = i if varias_suboperaciones else 0

    return PasoReproductor(
        indice=i, tipo="operacion", descripcion=desc,
        explicacion=expl, indice_grupo=grupo_idx,
        cuerpo=step, etiqueta_tipo=op_type, meta_explicar=meta,
    )


def _crear_grupos_matriz(pasos: list[PasoReproductor], total: int) -> list[GrupoReproductor]:
    """Crea la lista de grupos correspondientes a las operaciones."""
    if total == 1:
        return [
            GrupoReproductor(
                titulo="Operaciones de la expresión", resumen="1 operación",
                tipo="operacion", indices_pasos=(0,),
            )
        ]
    return [
        GrupoReproductor(
            titulo=paso.descripcion, resumen="1 operación",
            tipo="operacion", indices_pasos=(i,),
        )
        for i, paso in enumerate(pasos)
    ]


def construir_pasos_matrices(
    respuesta: dict,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Convierte segment_steps de la respuesta a estructuras inmutables del reproductor."""
    segment_steps = respuesta.get("segment_steps")
    if not segment_steps or not isinstance(segment_steps, list):
        return (), ()

    total = len(segment_steps)
    varias = total > 1
    pasos = [_crear_paso_matriz(i, step, total, varias) for i, step in enumerate(segment_steps)]
    grupos = _crear_grupos_matriz(pasos, total)

    return tuple(pasos), tuple(grupos)
