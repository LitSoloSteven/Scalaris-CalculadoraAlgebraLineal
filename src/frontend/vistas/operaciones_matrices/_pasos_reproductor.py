"""Adaptador puro de pasos_segmento al modelo del reproductor de pasos en Matrices."""

from __future__ import annotations

import re

from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.controladores.operaciones_matrices import (
    ControladorOperacionesMatrices,
)


def limpiar_descripcion_operacion(representacion_operacion: str | None, predeterminado: str) -> str:
    """Genera una versión legible y en texto plano de representacion_operacion."""
    if not representacion_operacion:
        return predeterminado
    termino = re.sub(r"_\{(\w+)\}", r"\1", str(representacion_operacion))
    termino = termino.replace(r"\cdot", "·").replace("{", "").replace("}", "").strip()
    return " ".join(termino.split())


def obtener_explicacion_operacion(tipo_operacion: str | None) -> str:
    """Devuelve una explicación concisa en español y tuteo según el tipo de operación."""
    termino = (tipo_operacion or "").lower()
    if "suma" in termino:
        return "Sumamos las matrices celda a celda."
    if "resta" in termino:
        return "Restamos las matrices celda a celda."
    if "escalar" in termino:
        return "Multiplicamos cada celda por el escalar."
    if "producto" in termino or "multiplicaci" in termino:
        return "Cada celda es el producto de una fila de A por una columna de B."
    if "transposi" in termino:
        return "Las filas pasan a ser columnas."
    if "negaci" in termino:
        return "Cambiamos el signo de cada celda."
    return "Aplicamos la operación celda a celda."


def _crear_paso_matriz(
    i: int, paso: dict, total: int, varias_suboperaciones: bool
) -> PasoReproductor:
    """Crea un paso del reproductor a partir del segmento de cálculo matricial."""
    tipo_operacion = paso.get("tipo_operacion") or "Operación"
    representacion = paso.get("representacion_operacion")
    descripcion = limpiar_descripcion_operacion(representacion, f"Operación {i + 1}")
    explicacion = obtener_explicacion_operacion(tipo_operacion)
    metadatos = ControladorOperacionesMatrices.construir_foco_paso(paso, i + 1, total)
    indice_grupo = i if varias_suboperaciones else 0

    return PasoReproductor(
        indice=i, tipo="operacion", descripcion=descripcion,
        explicacion=explicacion, indice_grupo=indice_grupo,
        cuerpo=paso, etiqueta_tipo=tipo_operacion, meta_explicar=metadatos,
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
    """Convierte pasos_segmento de la respuesta a estructuras inmutables del reproductor."""
    pasos_segmentos = respuesta.get("pasos_segmento")
    if not pasos_segmentos or not isinstance(pasos_segmentos, list):
        return (), ()

    total = len(pasos_segmentos)
    varias = total > 1
    pasos = [_crear_paso_matriz(i, paso, total, varias) for i, paso in enumerate(pasos_segmentos)]
    grupos = _crear_grupos_matriz(pasos, total)

    return tuple(pasos), tuple(grupos)
