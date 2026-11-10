"""Controles del rango visual independiente de los extremos del método."""
from nicegui import ui

from src.frontend.componentes.captura_exploracion_raices import campos_rango as campos_rango_raices
from .estado_captura import transaccion


def construir_rango(panel) -> None:
    """Monta extremos etiquetados, rango inicial explícito y copia voluntaria de a/b."""
    panel.minimo, panel.maximo = campos_rango("gráfico")
    ui.button("Ajustar al intervalo", color=None, on_click=panel.usar_intervalo).classes(
        "boton-discreto").props("ripple=false")


def campos_rango(contexto: str) -> tuple:
    """Monta los dos campos que representan el rango compartido en una tarea."""
    return campos_rango_raices(contexto, "biseccion-campos")


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


