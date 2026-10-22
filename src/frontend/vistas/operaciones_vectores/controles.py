"""Montaje de pestañas, entradas y acciones de la herramienta vectorial."""
from nicegui import ui
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.componentes.selector_opciones import SelectorOpciones
from src.frontend.textos import OPCIONES_OPERACIONES_VECTORES, NOMBRE_SELECTOR_VECTORES


def _actualizar_opcion(vista, nombre, valor):
    setattr(vista, nombre, valor)
    vista._al_cambiar_vectores()


def construir_suma_resta(vista):
    """Monta las opciones y celdas de suma y resta sin parsear entradas."""
    with ui.row().classes("w-full justify-between items-center panel-tarjeta p-4 vectores-operacion"):
        with ui.row().classes("gap-4 items-center vectores-operacion-selector"):
            ui.label("Operación:").classes("font-bold")
            vista.selector_operacion = ui.select(
                {"suma": "Suma", "resta": "Resta"}, value=vista.operacion_suma_resta,
                on_change=lambda evento: _actualizar_opcion(vista, "operacion_suma_resta", evento.value),
            ).classes("selector-controles vectores-operacion-campo").props('popup-content-class="selector-menu" aria-label="Operación vectorial"')
        vista.casilla_estricta = ui.checkbox(
            "Estricto (No auto-transponer)", value=vista.orientacion_estricta,
            on_change=lambda evento: _actualizar_opcion(vista, "orientacion_estricta", evento.value),
        ).classes("casilla-controles")
    vista.panel_suma_resta.construir(ui.column().classes("w-full"))


def construir_escalar(vista):
    """Monta el escalar y las celdas del vector que multiplicará."""
    with ui.row().classes("w-full items-center panel-tarjeta p-4 gap-4 vectores-operacion"):
        ui.label("Escalar (k):").classes("font-bold")
        vista.entrada_escalar = ui.input(
            value=vista.valor_escalar,
            on_change=lambda evento: _actualizar_opcion(vista, "valor_escalar", evento.value),
        ).classes("vectores-operacion-campo min-w-0 matriz-entrada").props('borderless aria-label="Escalar k"')
    vista.panel_escalar.construir(ui.column().classes("w-full"))


def _construir_pestanas(vista):
    with ui.row().classes("w-full mb-8"):
        vista.pestanas = SelectorOpciones(
            OPCIONES_OPERACIONES_VECTORES, vista.operacion_activa,
            vista.al_cambiar_pestana, NOMBRE_SELECTOR_VECTORES,
        )


def _construir_capturas(vista):
    with ui.column().classes("w-full bg-transparent p-0 vectores-paneles"):
        with vista.pestanas.asociar_contenido('suma_resta', ui.element('section').classes('w-full vectores-seccion')):
            construir_suma_resta(vista)
        with vista.pestanas.asociar_contenido('escalar', ui.element('section').classes('w-full vectores-seccion')):
            construir_escalar(vista)
        with vista.pestanas.asociar_contenido('combinacion_lineal', ui.element('section').classes('w-full vectores-seccion')):
            ui.markdown("Evalúa si el vector **b** es combinación lineal de los demás vectores.").classes("texto-secundario text-sm")
            vista.panel_combinacion.construir(ui.column().classes("w-full"))
        with vista.pestanas.asociar_contenido('independencia', ui.element('section').classes('w-full vectores-seccion')):
            ui.label("Comprueba si los vectores columna son independientes. No necesitas un vector objetivo.").classes("texto-secundario")
            vista.panel_independencia.construir(ui.column().classes("w-full"))
    for panel in vista.paneles.values():
        while len(panel.vectores) < panel.minimo_vectores:
            panel.agregar_vector()


def construir_panel_izquierdo(vista):
    """Monta pestañas, mínimos de captura y acciones de cálculo y limpieza."""
    with ui.column().classes("disposicion-panel vectores-panel-captura p-8 bg-[var(--bg-page)]"):
        _construir_pestanas(vista)
        _construir_capturas(vista)
        with ui.row().classes("w-full justify-between mt-8 pt-4 border-t border-[var(--border-input)] items-center"):
            crear_boton_limpieza(vista, lambda: vista._montada)
            vista.boton_calcular = ui.button(
                "Calcular", icon="calculate", on_click=vista.calcular, color=None,
            ).classes("boton-principal flex-[2] py-3 font-bold")
