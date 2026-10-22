"""Funciones de renderizado de resultados y condicion de Hawkins-Simon para Leontief."""
from __future__ import annotations

import html
from nicegui import ui
from src.frontend.componentes.avisos_resultado import CLASES_AVISO_ERROR, renderizar_aviso_resultado
from src.frontend.componentes.desarrollo_comprobacion import mostrar_desarrollo


def renderizar_resultado_leontief(resultado: dict) -> None:
    """Renderiza tarjetas de resultado para el modelo de Leontief."""
    estado = resultado.get("estado")

    if estado == "ERROR":
        renderizar_aviso_resultado(resultado.get("mensaje", "Error"), "close", CLASES_AVISO_ERROR)
        return

    if estado in {"SINGULAR", "SIN_SOLUCION", "SOLUCIONES_INFINITAS"}:
        with ui.row().classes("items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit"):
            ui.icon("warning_amber", size="sm")
            ui.label(resultado.get("mensaje")).classes("font-bold")
        condicion = resultado.get("hawkins_simon", {})
        if condicion:
            renderizar_hawkins_simon(condicion)
        mostrar_desarrollo(resultado.get("traza_comprobacion", []))
        return

    with ui.row().classes("items-center gap-2 px-4 py-2 distintivo-exito mb-4 w-fit"):
        ui.icon("check", size="sm")
        ui.label(resultado.get("mensaje", "")).classes("font-bold")

    renderizar_hawkins_simon(resultado.get("hawkins_simon", {}))

    with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
        ui.label("Matriz de Leontief  M = I - C").classes("font-bold texto-principal mb-2")
        matriz_latex = html.escape(resultado.get("matriz_leontief_latex", ""))
        ui.html(f'<div class="matematicas-desplazamiento matematicas-etiqueta text-xl text-center">$$ M = {matriz_latex} $$</div>')

    with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
        ui.label("Multiplicador de Leontief  (I - C)^(-1)").classes("font-bold texto-principal mb-2")
        multiplicador_latex = html.escape(resultado.get("matriz_multiplicador_latex", ""))
        ui.html(f'<div class="matematicas-desplazamiento matematicas-etiqueta text-xl text-center">$$ (I-C)^{{-1}} = {multiplicador_latex} $$</div>')

    _renderizar_vector_produccion(resultado)
    _renderizar_analisis_sectorial(resultado)
    mostrar_desarrollo(resultado.get("traza_comprobacion", []))


def _renderizar_vector_produccion(resultado: dict) -> None:
    """Muestra el vector de produccion x con desglose de demanda."""
    with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
        ui.label("Vector de producción  x = (I - C)^(-1) · d").classes("font-bold texto-principal mb-3")
        sectores = resultado.get("nombres_sectores", [])
        producciones = resultado.get("vector_produccion", [])
        demandas = resultado.get("vector_demanda", [])
        with ui.column().classes("w-full gap-2"):
            for sector, producto, demanda in zip(sectores, producciones, demandas):
                _renderizar_sector_produccion(sector, producto, demanda)


def _renderizar_sector_produccion(sector, producto, demanda):
    """Presenta la demanda y producción del sector con su nombre completo como ayuda."""
    with ui.row().classes("w-full items-center gap-3 panel-tarjeta p-3 flex-wrap"):
        etiqueta = ui.label(sector).classes("font-bold texto-principal min-w-0 max-w-full truncate")
        etiqueta._props["title"] = sector
        with ui.column().classes("gap-0"):
            ui.html(f'<span class="text-sm texto-secundario">Demanda final: <b>{html.escape(demanda)}</b></span>')
            ui.html(f'<span class="font-bold texto-acento">Producción total: {html.escape(producto)}</span>')


def _renderizar_analisis_sectorial(resultado: dict) -> None:
    """Muestra la tabla de analisis sectorial."""
    analisis = resultado.get("analisis_sectorial", [])
    if not analisis:
        return
    with ui.column().classes("w-full panel-tarjeta p-4 mb-4 modelos-sectorial"):
        ui.label("Análisis Sectorial").classes("font-bold texto-principal mb-3")
        with (
            ui.expansion("Ver desglose por sector", icon="table_chart").classes("w-full").props('header-class="font-bold texto-principal"'),
            ui.column().classes("w-full gap-2 mt-2"),
        ):
            _renderizar_cabecera_sectorial()
            for fila in analisis:
                _renderizar_fila_analisis(fila)


def _renderizar_cabecera_sectorial():
    """Presenta los nombres de las cinco columnas del análisis sectorial."""
    encabezados = ["Sector", "Producción Total", "Insumos Intermedios", "Demanda Final", "Valor Añadido"]
    with ui.row().classes("gap-3 w-full"):
        for encabezado in encabezados:
            ui.label(encabezado).classes("text-xs font-bold texto-secundario uppercase tracking-wide flex-1")


def _renderizar_fila_analisis(fila):
    """Presenta las cinco magnitudes del sector sin truncar los valores numéricos."""
    with ui.row().classes("w-full gap-3 panel-tarjeta p-2"):
        etiqueta = ui.label(fila["sector"]).classes("font-bold texto-principal flex-1 text-sm min-w-0 truncate")
        etiqueta._props["title"] = fila["sector"]
        ui.label(fila["produccion_total"]).classes("flex-1 text-sm break-all")
        ui.label(fila["consumo_intermedio"]).classes("flex-1 text-sm break-all")
        ui.label(fila["demanda_final"]).classes("flex-1 text-sm break-all")
        ui.label(fila["valor_anadido"]).classes("flex-1 text-sm break-all")


def renderizar_hawkins_simon(condicion: dict) -> None:
    """Muestra el resultado de la condicion de viabilidad economica de Hawkins-Simon."""
    if not condicion:
        return
    viable = condicion.get("es_economicamente_viable", False)
    distintivo = "distintivo-exito" if viable else "distintivo-advertencia"
    icono = "verified" if viable else "warning_amber"
    with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
        with ui.row().classes(f"items-center gap-2 px-4 py-2 {distintivo} mb-3 w-fit"):
            ui.icon(icono, size="sm")
            texto = "Condición de Hawkins-Simon: SATISFECHA ✓" if viable else "Condición de Hawkins-Simon: NO satisfecha ✗"
            if condicion.get("criterio_aplicable") is False:
                texto = "Condición de Hawkins-Simon: NO APLICABLE"
            ui.label(texto).classes("font-bold")
        ui.label(condicion.get("conclusion", "")).classes("text-sm texto-secundario mb-2")
        menores = condicion.get("menores_principales", [])
        if menores:
            with ui.row().classes("gap-2 flex-wrap mt-2"):
                _renderizar_menores(menores)


def _renderizar_menores(menores):
    """Presenta el determinante de cada menor e indica si es positivo."""
    for menor in menores:
        distintivo_menor = "distintivo-exito" if menor["es_positivo"] else "distintivo-error"
        ui.html(
            f'<span class="px-3 py-1 rounded-full text-xs font-bold {distintivo_menor}">'
            f'Δ<sub>{menor["orden"]}</sub> = {html.escape(menor["determinante"])}</span>'
        )
