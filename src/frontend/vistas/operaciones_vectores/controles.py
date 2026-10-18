"""Montaje de pestañas, entradas y acciones de la herramienta vectorial."""
from nicegui import ui


def _actualizar_opcion(vista, nombre, valor):
    setattr(vista, nombre, valor)
    vista._al_cambiar_vectores()


def construir_suma_resta(vista):
    """Monta las opciones y celdas de suma y resta sin parsear entradas."""
    with ui.row().classes("w-full justify-between items-center mb-4 panel-tarjeta p-4"):
        with ui.row().classes("gap-4 items-center"):
            ui.label("Operación:").classes("font-bold")
            vista.selector_operacion = ui.select(
                {"suma": "Suma", "resta": "Resta"}, value=vista.operacion_suma_resta,
                on_change=lambda evento: _actualizar_opcion(vista, "operacion_suma_resta", evento.value),
            ).classes("selector-controles w-44").props('popup-content-class="selector-menu" aria-label="Operación vectorial"')
        vista.casilla_estricta = ui.checkbox(
            "Estricto (No auto-transponer)", value=vista.orientacion_estricta,
            on_change=lambda evento: _actualizar_opcion(vista, "orientacion_estricta", evento.value),
        ).classes("casilla-controles")
    vista.panel_suma_resta.construir(ui.column().classes("w-full"))


def construir_escalar(vista):
    """Monta el escalar y las celdas del vector que multiplicará."""
    with ui.row().classes("w-full items-center mb-4 panel-tarjeta p-4 gap-4"):
        ui.label("Escalar (k):").classes("font-bold")
        vista.entrada_escalar = ui.input(
            value=vista.valor_escalar,
            on_change=lambda evento: _actualizar_opcion(vista, "valor_escalar", evento.value),
        ).classes("w-32 min-w-0 matriz-entrada").props('borderless aria-label="Escalar k"')
    vista.panel_escalar.construir(ui.column().classes("w-full"))


def _construir_pestanas(vista):
    with ui.row().classes("w-full justify-between items-center mb-8 gap-4 flex-wrap"):
        with ui.tabs().classes("pestanas-controles pestanas-vectores").props(
            'no-caps mobile-arrows outside-arrows align="left" aria-label="Operaciones con vectores"'
        ) as vista.pestanas:
            ui.tab("suma_resta", label="Suma / Resta")
            ui.tab("escalar", label="Escalar × Vector")
            ui.tab("combinacion_lineal", label="Combinación Lineal")
        vista.pestanas.value = vista.operacion_activa
        vista.pestanas.on_value_change(vista.al_cambiar_pestana)


def _construir_capturas(vista):
    with ui.tab_panels(vista.pestanas, value=vista.operacion_activa).classes("w-full bg-transparent p-0 flex-1"):
        with ui.tab_panel("suma_resta").classes("p-0"):
            construir_suma_resta(vista)
        with ui.tab_panel("escalar").classes("p-0"):
            construir_escalar(vista)
        with ui.tab_panel("combinacion_lineal").classes("p-0"):
            ui.markdown("Evalúa si el vector **b** es combinación lineal de los demás vectores.").classes("mb-4 texto-secundario text-sm")
            vista.panel_combinacion.construir(ui.column().classes("w-full"))
    for panel in vista.paneles.values():
        while len(panel.vectores) < panel.minimo_vectores:
            panel.agregar_vector()


def construir_panel_izquierdo(vista):
    """Monta pestañas, mínimos de captura y acciones de cálculo y limpieza."""
    with ui.column().classes("disposicion-panel vectores-panel-captura p-8 bg-[var(--bg-page)]"):
        _construir_pestanas(vista)
        _construir_capturas(vista)
        with ui.row().classes("w-full justify-between mt-8 pt-4 border-t border-[var(--border-input)] items-center"):
            ui.button("Limpiar", icon="delete", on_click=vista.limpiar, color=None).classes("boton-discreto").props('ripple=false id="boton-limpiar-principal"')
            vista.boton_calcular = ui.button(
                "Calcular", icon="calculate", on_click=vista.calcular, color=None,
            ).classes("boton-principal px-8 py-2 font-bold")
