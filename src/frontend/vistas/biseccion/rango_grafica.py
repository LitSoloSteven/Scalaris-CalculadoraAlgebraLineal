"""Controles del rango visual independiente de los extremos del método."""
from nicegui import ui

from src.frontend.controladores.biseccion.vista_previa import LONGITUD_CAMPO_GRAFICA, RANGO_GRAFICA_DEFECTO
from .estado_captura import transaccion


def construir_rango(panel) -> None:
    """Monta extremos etiquetados, rango inicial explícito y copia voluntaria de a/b."""
    panel.minimo, panel.maximo = campos_rango("gráfico")
    ui.button("Ajustar al intervalo", color=None, on_click=panel.usar_intervalo).classes(
        "boton-discreto").props("ripple=false")


def campos_rango(contexto: str) -> tuple:
    """Monta los dos campos que representan el rango compartido en una tarea."""
    with ui.element("div").classes("biseccion-campos"):
        minimo = _campo(f"Mínimo del {contexto}", RANGO_GRAFICA_DEFECTO[0])
        maximo = _campo(f"Máximo del {contexto}", RANGO_GRAFICA_DEFECTO[1])
    return minimo, maximo


def sincronizar_rango(vista, valores: tuple) -> None:
    """Escribe ambos extremos en las dos tareas y emite un único cambio efectivo."""
    previa, exploracion = vista.vista_previa, vista.exploracion
    with transaccion(vista):
        for panel in (previa, exploracion):
            panel.minimo.set_value(valores[0])
            panel.maximo.set_value(valores[1])
    exploracion.actualizar_paso()
    exploracion.invalidar()
    previa.programar()


def _campo(etiqueta: str, valor: int):
    return ui.input(etiqueta, value=str(valor)).classes("w-full matriz-entrada").props(
        f"inputmode=decimal maxlength={LONGITUD_CAMPO_GRAFICA} autocomplete=off")
