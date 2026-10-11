"""Renderizado de resultados y propiedades para la vista de Transformaciones Lineales."""
from __future__ import annotations

import html
from nicegui import ui


def renderizar_resultado_transformaciones(r: dict) -> None:
    """Renderiza todas las secciones analiticas de la transformacion lineal."""
    status = r.get("status")
    if status == "ERROR":
        with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
            ui.icon("close", size="sm")
            ui.label(r.get("message", "Error")).classes("font-bold")
        return

    m, n = r.get("m"), r.get("n")
    rango = r.get("rango")
    nulidad = r.get("nulidad")

    with ui.row().classes("items-center gap-2 px-4 py-2 badge-success mb-4 w-fit"):
        ui.icon("check", size="sm")
        ui.label(r.get("message", "")).classes("font-bold")

    callout = r.get("callout_convencion", "")
    if callout:
        with ui.row().classes("w-full items-start gap-2 px-4 py-3 rounded-lg mb-4").style(
            "background: var(--bg-accent-subtle, rgba(var(--accent-rgb), 0.08)); "
            "border-left: 3px solid var(--accent);"
        ):
            ui.icon("info", size="sm").classes("text-accent mt-0.5 flex-shrink-0")
            ui.label(callout).classes("text-xs text-sec")

    _renderizar_metricas_dimension(r, m, n, rango, nulidad)
    _renderizar_conclusiones(r)
    _renderizar_nucleo(r, nulidad)
    _renderizar_imagen(r, rango)
    _renderizar_pasos(r)


def _renderizar_metricas_dimension(r: dict, m: int, n: int, rango: int, nulidad: int) -> None:
    """Muestra tarjetas de rango, nulidad y el Teorema de la Dimension."""
    with ui.row().classes("w-full gap-4 mb-4 flex-wrap"):
        for label, val, color_class in [
            ("Rango", rango, "text-accent"),
            ("Nulidad", nulidad, "text-sec"),
            (f"T: R^{n} -> R^{m}", "", ""),
        ]:
            with ui.column().classes("panel-card p-4 flex-1 items-center text-center gap-1"):
                if val != "":
                    ui.label(str(val)).classes(f"text-3xl font-bold {color_class}")
                ui.label(label).classes("text-sm text-sec")

    with ui.row().classes("w-full panel-card p-3 mb-4 items-center gap-2"):
        ui.icon("functions", size="sm").classes("text-accent")
        ui.html(
            f'<span class="font-bold text-main">Teorema de la Dimension:</span> '
            f'<span class="text-sec">{html.escape(r.get("teorema_dimension", ""))}</span>'
        )


def _renderizar_conclusiones(r: dict) -> None:
    """Muestra las propiedades de inyectividad y sobreyectividad."""
    conclusiones = r.get("conclusiones", {})
    with ui.column().classes("w-full panel-card p-4 mb-4 gap-2"):
        ui.label("Propiedades de T").classes("font-bold text-main mb-1")
        for _, texto in conclusiones.items():
            if texto:
                badge = "badge-success" if ("es INYECTIVA" in texto or "es SOBREYECTIVA" in texto or "BIYECTIVA" in texto) else "badge-warning"
                with ui.row().classes(f"items-center gap-2 px-3 py-2 {badge} w-fit rounded"):
                    ui.label(texto).classes("text-sm font-bold")


def _renderizar_nucleo(r: dict, nulidad: int) -> None:
    """Muestra la base del nucleo (ker T)."""
    base_nucleo = r.get("base_nucleo", [])
    with ui.column().classes("w-full panel-card p-4 mb-4"):
        ui.label(f"Nucleo  ker(T)  [dim = {nulidad}]").classes("font-bold text-main mb-2")
        if not base_nucleo:
            ui.html('<div class="math-scroll-container math-label text-lg text-center">$$ \\ker(T) = \\{\\mathbf{0}\\} $$</div>')
        else:
            for vec_info in base_nucleo:
                param = vec_info["parametro"]
                vec = vec_info["vector"]
                vec_tex = r"\begin{pmatrix} " + r" \\ ".join(html.escape(v) for v in vec) + r" \end{pmatrix}"
                ui.html(f'<div class="math-scroll-container math-label text-lg text-center">$$ \\mathbf{{v}}_{{{html.escape(param)}}} = {vec_tex} $$</div>')


def _renderizar_imagen(r: dict, rango: int) -> None:
    """Muestra la base de la imagen (Im T)."""
    base_imagen = r.get("base_imagen", [])
    with ui.column().classes("w-full panel-card p-4 mb-4"):
        ui.label(f"Imagen  Im(T)  [dim = {rango}]").classes("font-bold text-main mb-2")
        ui.html('<p class="text-xs text-sec mb-2">Base formada por las columnas pivote de A (convencion columna estandar).</p>')
        if not base_imagen:
            ui.label("Imagen = {0}").classes("text-sec italic")
        else:
            for vec_info in base_imagen:
                idx = vec_info["indice_columna"]
                vec = vec_info["vector"]
                vec_tex = r"\begin{pmatrix} " + r" \\ ".join(html.escape(v) for v in vec) + r" \end{pmatrix}"
                ui.html(f'<div class="math-scroll-container math-label text-lg text-center">$$ \\mathbf{{a}}_{{{idx}}} = {vec_tex} $$</div>')


def _renderizar_pasos(r: dict) -> None:
    """Expansion con los pasos de reduccion Gauss-Jordan."""
    pasos = r.get("pasos_reduccion", [])
    if pasos:
        with ui.expansion("Ver reduccion Gauss-Jordan de A", icon="visibility").classes(
            "w-full panel-card mt-4 timeline-expansion"
        ).props('header-class="font-bold text-main"'):
            for paso in pasos:
                with ui.column().classes(
                    "w-full p-4 border-l-2 border-l-[var(--accent)] ml-2 mb-2 bg-[var(--bg-panel)] rounded-r-lg"
                ):
                    ui.label(paso["descripcion"]).classes("text-sm font-semibold mb-1 text-sec")
                    ui.html(f'<div class="math-scroll-container math-label text-lg">$$ {paso["matriz"]} $$</div>')
