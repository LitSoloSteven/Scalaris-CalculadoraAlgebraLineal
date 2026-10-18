"""Renderizado de resultados y propiedades para la vista de Transformaciones Lineales."""
from __future__ import annotations

import html
from nicegui import ui
from src.frontend.componentes.avisos_resultado import CLASES_AVISO_ERROR, renderizar_aviso_resultado


def renderizar_resultado_transformaciones(resultado: dict) -> None:
    """Renderiza todas las secciones analiticas de la transformacion lineal."""
    estado = resultado.get("estado")
    if estado == "ERROR":
        renderizar_aviso_resultado(resultado.get("mensaje", "Error"), "close", CLASES_AVISO_ERROR)
        return

    filas, columnas = resultado.get("dimension_codominio"), resultado.get("dimension_dominio")
    rango = resultado.get("rango")
    nulidad = resultado.get("nulidad")

    with ui.row().classes("items-center gap-2 px-4 py-2 distintivo-exito mb-4 w-fit"):
        ui.icon("check", size="sm")
        ui.label(resultado.get("mensaje", "")).classes("font-bold")

    aviso = resultado.get("aviso_convencion", "")
    if aviso:
        with ui.row().classes("w-full items-start gap-2 px-4 py-3 rounded-lg mb-4 modelos-aviso"):
            ui.icon("info", size="sm").classes("texto-acento mt-0.5 flex-shrink-0")
            ui.label(aviso).classes("text-xs texto-secundario")

    _renderizar_metricas_dimension(resultado, filas, columnas, rango, nulidad)
    _renderizar_conclusiones(resultado)
    _renderizar_nucleo(resultado, nulidad)
    _renderizar_imagen(resultado, rango)
    _renderizar_pasos(resultado)


def _renderizar_metricas_dimension(resultado: dict, filas: int, columnas: int, rango: int, nulidad: int) -> None:
    """Muestra tarjetas de rango, nulidad y el Teorema de la Dimension."""
    with ui.row().classes("w-full gap-4 mb-4 flex-wrap"):
        for etiqueta, valor, clase_color in [
            ("Rango", rango, "texto-acento"),
            ("Nulidad", nulidad, "texto-secundario"),
            (f"T: R^{columnas} -> R^{filas}", "", ""),
        ]:
            _renderizar_metrica(etiqueta, valor, clase_color)

    with ui.row().classes("w-full panel-tarjeta p-3 mb-4 items-center gap-2"):
        ui.icon("functions", size="sm").classes("texto-acento")
        ui.html(
            f'<span class="font-bold texto-principal">Teorema de la Dimension:</span> '
            f'<span class="texto-secundario">{html.escape(resultado.get("teorema_dimension", ""))}</span>'
        )


def _renderizar_metrica(etiqueta, valor, clase_color):
    """Presenta una magnitud y su etiqueta con la clase de color indicada."""
    with ui.column().classes("panel-tarjeta p-4 flex-1 items-center text-center gap-1"):
        if valor != "":
            ui.label(str(valor)).classes(f"text-3xl font-bold {clase_color}")
        ui.label(etiqueta).classes("text-sm texto-secundario")


def _renderizar_conclusiones(resultado: dict) -> None:
    """Muestra las propiedades de inyectividad y sobreyectividad."""
    conclusiones = resultado.get("conclusiones", {})
    with ui.column().classes("w-full panel-tarjeta p-4 mb-4 gap-2"):
        ui.label("Propiedades de T").classes("font-bold texto-principal mb-1")
        for _, texto in conclusiones.items():
            if texto:
                distintivo = "distintivo-exito" if ("es INYECTIVA" in texto or "es SOBREYECTIVA" in texto or "BIYECTIVA" in texto) else "distintivo-advertencia"
                _renderizar_conclusion(texto, distintivo)


def _renderizar_conclusion(texto, distintivo):
    """Presenta la conclusión recibida con el distintivo de clasificación indicado."""
    with ui.row().classes(f"items-center gap-2 px-3 py-2 {distintivo} w-fit rounded"):
        ui.label(texto).classes("text-sm font-bold")


def _renderizar_nucleo(resultado: dict, nulidad: int) -> None:
    """Muestra la base del nucleo (ker T)."""
    base_nucleo = resultado.get("base_nucleo", [])
    with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
        ui.label(f"Nucleo  ker(T)  [dim = {nulidad}]").classes("font-bold texto-principal mb-2")
        if not base_nucleo:
            ui.html('<div class="matematicas-desplazamiento matematicas-etiqueta text-lg text-center">$$ \\ker(T) = \\{\\mathbf{0}\\} $$</div>')
        else:
            for datos_vector in base_nucleo:
                parametro = datos_vector["parametro"]
                vector = datos_vector["vector"]
                vector_latex = r"\begin{pmatrix} " + r" \\ ".join(html.escape(componente) for componente in vector) + r" \end{pmatrix}"
                ui.html(f'<div class="matematicas-desplazamiento matematicas-etiqueta text-lg text-center">$$ \\mathbf{{v}}_{{{html.escape(parametro)}}} = {vector_latex} $$</div>')


def _renderizar_imagen(resultado: dict, rango: int) -> None:
    """Muestra la base de la imagen (Im T)."""
    base_imagen = resultado.get("base_imagen", [])
    with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
        ui.label(f"Imagen  Im(T)  [dim = {rango}]").classes("font-bold texto-principal mb-2")
        ui.html('<p class="text-xs texto-secundario mb-2">Base formada por las columnas pivote de A (convencion columna estandar).</p>')
        if not base_imagen:
            ui.label("Imagen = {0}").classes("texto-secundario italic")
        else:
            for datos_vector in base_imagen:
                indice = datos_vector["indice_columna"]
                vector = datos_vector["vector"]
                vector_latex = r"\begin{pmatrix} " + r" \\ ".join(html.escape(componente) for componente in vector) + r" \end{pmatrix}"
                ui.html(f'<div class="matematicas-desplazamiento matematicas-etiqueta text-lg text-center">$$ \\mathbf{{a}}_{{{indice}}} = {vector_latex} $$</div>')


def _renderizar_pasos(resultado: dict) -> None:
    """Expansion con los pasos de reduccion Gauss-Jordan."""
    pasos = resultado.get("pasos_reduccion", [])
    if pasos:
        with ui.expansion("Ver reduccion Gauss-Jordan de A", icon="visibility").classes(
            "w-full panel-tarjeta mt-4 pasos-expansion"
        ).props('header-class="font-bold texto-principal"'):
            for paso in pasos:
                _renderizar_paso_reduccion(paso)


def _renderizar_paso_reduccion(paso):
    """Presenta la descripción y matriz de un paso de reducción."""
    with ui.column().classes(
        "w-full p-4 border-l-2 border-l-[var(--accent)] ml-2 mb-2 bg-[var(--bg-panel)] rounded-r-lg"
    ):
        ui.label(paso["descripcion"]).classes("text-sm font-semibold mb-1 texto-secundario")
        ui.html(f'<div class="matematicas-desplazamiento matematicas-etiqueta text-lg">$$ {paso["matriz"]} $$</div>')
