"""Funciones de renderizado de resultados y condicion de Hawkins-Simon para Leontief."""
from __future__ import annotations

import html
from nicegui import ui


def renderizar_resultado_leontief(r: dict) -> None:
    """Renderiza tarjetas de resultado para el modelo de Leontief."""
    status = r.get("status")

    if status == "ERROR":
        with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
            ui.icon("close", size="sm")
            ui.label(r.get("message", "Error")).classes("font-bold")
        return

    if status == "SINGULAR":
        with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
            ui.icon("warning_amber", size="sm")
            ui.label(r.get("message")).classes("font-bold")
        hs = r.get("hawkins_simon", {})
        if hs:
            renderizar_hawkins_simon(hs)
        return

    with ui.row().classes("items-center gap-2 px-4 py-2 badge-success mb-4 w-fit"):
        ui.icon("check", size="sm")
        ui.label(r.get("message", "")).classes("font-bold")

    renderizar_hawkins_simon(r.get("hawkins_simon", {}))

    with ui.column().classes("w-full panel-card p-4 mb-4"):
        ui.label("Matriz de Leontief  M = I - C").classes("font-bold text-main mb-2")
        m_tex = html.escape(r.get("matriz_leontief_latex", ""))
        ui.html(f'<div class="math-scroll-container math-label text-xl text-center">$$ M = {m_tex} $$</div>')

    with ui.column().classes("w-full panel-card p-4 mb-4"):
        ui.label("Multiplicador de Leontief  (I - C)^(-1)").classes("font-bold text-main mb-2")
        mul_tex = html.escape(r.get("matriz_multiplicador_latex", ""))
        ui.html(f'<div class="math-scroll-container math-label text-xl text-center">$$ (I-C)^{{-1}} = {mul_tex} $$</div>')

    _renderizar_vector_produccion(r)
    _renderizar_analisis_sectorial(r)


def _renderizar_vector_produccion(r: dict) -> None:
    """Muestra el vector de produccion x con desglose de demanda."""
    with ui.column().classes("w-full panel-card p-4 mb-4"):
        ui.label("Vector de producción  x = (I - C)^(-1) · d").classes("font-bold text-main mb-3")
        sectores = r.get("sectores", [])
        prods = r.get("vector_produccion", [])
        dems = r.get("vector_demanda", [])
        with ui.column().classes("w-full gap-2"):
            for sect, prod, dem in zip(sectores, prods, dems):
                with ui.row().classes("w-full items-center gap-3 panel-card p-3"):
                    ui.label(sect).classes("font-bold text-main min-w-[100px]")
                    with ui.column().classes("gap-0"):
                        ui.html(f'<span class="text-sm text-sec">Demanda final: <b>{html.escape(dem)}</b></span>')
                        ui.html(f'<span class="font-bold text-accent">Producción total: {html.escape(prod)}</span>')


def _renderizar_analisis_sectorial(r: dict) -> None:
    """Muestra la tabla de analisis sectorial."""
    analisis = r.get("analisis_sectorial", [])
    if not analisis:
        return
    with ui.column().classes("w-full panel-card p-4 mb-4"):
        ui.label("Análisis Sectorial").classes("font-bold text-main mb-3")
        with ui.expansion("Ver desglose por sector", icon="table_chart").classes("w-full").props('header-class="font-bold text-main"'):
            with ui.column().classes("w-full gap-2 mt-2"):
                headers = ["Sector", "Producción Total", "Insumos Intermedios", "Demanda Final", "Valor Añadido"]
                with ui.row().classes("gap-3 w-full"):
                    for h in headers:
                        ui.label(h).classes("text-xs font-bold text-sec uppercase tracking-wide flex-1")
                for fila in analisis:
                    with ui.row().classes("w-full gap-3 panel-card p-2"):
                        ui.label(fila["sector"]).classes("font-bold text-main flex-1 text-sm")
                        ui.label(fila["produccion_total"]).classes("flex-1 text-sm")
                        ui.label(fila["insumos_intermedios"]).classes("flex-1 text-sm")
                        ui.label(fila["demanda_final"]).classes("flex-1 text-sm")
                        ui.label(fila["valor_anadido"]).classes("flex-1 text-sm")


def renderizar_hawkins_simon(hs: dict) -> None:
    """Muestra el resultado de la condicion de viabilidad economica de Hawkins-Simon."""
    if not hs:
        return
    viable = hs.get("viable", False)
    badge = "badge-success" if viable else "badge-warning"
    icon = "verified" if viable else "warning_amber"
    with ui.column().classes("w-full panel-card p-4 mb-4"):
        with ui.row().classes(f"items-center gap-2 px-4 py-2 {badge} mb-3 w-fit"):
            ui.icon(icon, size="sm")
            texto = "Condición de Hawkins-Simon: SATISFECHA ✓" if viable else "Condición de Hawkins-Simon: NO satisfecha ✗"
            ui.label(texto).classes("font-bold")
        ui.label(hs.get("conclusion", "")).classes("text-sm text-sec mb-2")
        menores = hs.get("menores", [])
        if menores:
            with ui.row().classes("gap-2 flex-wrap mt-2"):
                for m in menores:
                    badge_m = "badge-success" if m["positivo"] else "badge-error"
                    ui.html(
                        f'<span class="px-3 py-1 rounded-full text-xs font-bold {badge_m}">'
                        f'Δ<sub>{m["orden"]}</sub> = {html.escape(m["determinante"])}</span>'
                    )
