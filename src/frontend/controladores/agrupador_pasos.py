"""Agrupación y clasificación didáctica de pasos de eliminación por filas."""
from typing import Any

from src.frontend.controladores.clasificador_pasos import clasificar_paso
from src.frontend.controladores.manejadores_pasos import (
    ContextoPasos,
    construir_titulo_columna,
    manejar_eliminacion,
    manejar_inicial,
    manejar_intercambio,
    manejar_normalizacion,
    manejar_otro,
    manejar_pivote,
)


def _formatear_grupos_finales(grupos_crudos: list[dict]) -> list[dict]:
    """Convierte los grupos acumulados al contrato estructurado para la interfaz."""
    grupos = []
    for g in grupos_crudos:
        k = len(g["step_indices"])
        resumen = "1 operación" if k == 1 else f"{k} operaciones"
        g_kind = g.get("kind", "otro")
        titulo = construir_titulo_columna(g) if g_kind == "columna" else g.get("title", "")
        grupos.append({
            "title": titulo,
            "summary": resumen,
            "kind": g_kind,
            "step_indices": g["step_indices"],
        })
    return grupos


def _despachar_paso(
    idx: int,
    paso_item: dict,
    parsed: dict,
    ctx: ContextoPasos,
    estado_grupos: tuple[list[dict], dict],
) -> tuple[dict, int]:
    """Despacha el paso según su tipo y actualiza los grupos de columna y normalización."""
    grupos_crudos, estado = estado_grupos
    kind = parsed["kind"]
    desc = paso_item.get("description", "")
    mat = paso_item.get("matrix")

    if kind == "inicial":
        estado["col"], estado["norm"], estado["otro"] = None, None, None
        return manejar_inicial(idx, ctx, grupos_crudos)
    if kind == "intercambio":
        estado["norm"], estado["otro"] = None, None
        return manejar_intercambio(idx, parsed, grupos_crudos, estado)
    if kind == "pivote":
        estado["norm"], estado["otro"] = None, None
        return manejar_pivote(idx, parsed, mat, ctx, estado_grupos)
    if kind == "eliminacion":
        estado["norm"] = None
        return manejar_eliminacion(idx, parsed, ctx, grupos_crudos, estado)
    if kind == "normalizacion":
        estado["col"], estado["otro"] = None, None
        return manejar_normalizacion(idx, parsed, ctx, grupos_crudos, estado)
    return manejar_otro(idx, desc, grupos_crudos, estado)


def _ensamblar_paso(
    idx: int,
    paso_item: dict,
    datos_paso: tuple[dict, int],
    ctx: ContextoPasos,
    es_ultimo: bool,
) -> dict:
    """Construye el diccionario del paso individual con su explicación."""
    datos, g_idx = datos_paso
    desc = paso_item.get("description", "")
    mat = paso_item.get("matrix")
    explicacion = datos["explanation"]
    if ctx.contexto == "inversa" and es_ultimo and ctx.estado_resp == "SUCCESS":
        explicacion = (
            "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque "
            "derecho es A⁻¹. " + explicacion
        )
    return {
        "index": idx,
        "description": desc,
        "kind": paso_item.get("kind", datos.get("kind", "")),
        "group_index": g_idx,
        "pivot": datos["pivot"],
        "rows_changed": datos["rows_changed"],
        "swap_rows": datos["swap_rows"],
        "explanation": explicacion,
        "matrix": mat,
    }


def agrupar_pasos_eliminacion(
    pasos_crudos: list[dict],
    n_izq: int,
    estado: str | None,
    *,
    contexto: str,
    metodo: str | None = None,
) -> tuple[list[dict], list[dict], dict]:
    """Clasifica los pasos de eliminación, asigna explicaciones y los agrupa por fases."""
    pasos: list[dict] = []
    grupos_crudos: list[dict] = []
    estado_dict: dict = {"col": None, "norm": None, "otro": None}
    estado_grupos = (grupos_crudos, estado_dict)
    ctx = ContextoPasos(
        contexto=contexto,
        n_izq=n_izq,
        es_gauss=(str(metodo).lower() == "gauss"),
        estado_resp=estado,
    )
    total = len(pasos_crudos)

    for idx, paso_item in enumerate(pasos_crudos):
        parsed = clasificar_paso(paso_item.get("description", ""))
        datos_paso = _despachar_paso(idx, paso_item, parsed, ctx, estado_grupos)
        item_con_tipo = {**paso_item, "kind": parsed["kind"]}
        pasos.append(_ensamblar_paso(idx, item_con_tipo, datos_paso, ctx, idx == total - 1))

    grupos = _formatear_grupos_finales(grupos_crudos)
    stats = {
        "total": len(pasos),
        "pivotes": sum(1 for s in pasos if s["kind"] == "pivote"),
        "intercambios": sum(1 for s in pasos if s["kind"] == "intercambio"),
        "eliminaciones": sum(1 for s in pasos if s["kind"] == "eliminacion"),
        "normalizaciones": sum(1 for s in pasos if s["kind"] == "normalizacion"),
    }
    return pasos, grupos, stats
