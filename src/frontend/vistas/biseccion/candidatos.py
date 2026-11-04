"""Lista accesible de registros de exploración con carga explícita de intervalos aptos."""
from nicegui import ui

from src.frontend.controladores.biseccion.exploracion import presentar_candidato


def mostrar_candidatos(panel, respuesta: dict) -> None:
    """Compone avisos y candidatos; los registros no aptos solo permiten inspección textual."""
    for advertencia in respuesta["advertencias"]:
        ui.label(advertencia).classes("text-sm texto-secundario")
    ui.label(f"Evaluaciones: {respuesta['evaluaciones']} · Registros: {len(respuesta['candidatos'])}").classes(
        "biseccion-numero texto-secundario")
    if not respuesta["candidatos"]:
        ui.label("No se detectaron candidatos en esta malla. Reduce el paso o cambia el rango para explorar de nuevo.").classes(
            "texto-secundario")
    ui.label("Bisección obtiene como máximo una aproximación por cálculo. Carga un intervalo y después pide calcular.").classes(
        "text-sm texto-secundario")
    for indice, candidato in enumerate(respuesta["candidatos"], 1):
        _mostrar_candidato(panel, respuesta, (indice, candidato))


def _mostrar_candidato(panel, respuesta: dict, registro: tuple) -> None:
    indice, candidato = registro
    datos = presentar_candidato(candidato)
    with ui.column().classes("biseccion-candidato w-full gap-2"):
        ui.label(f"{indice}. {datos['etiqueta']}").classes("font-semibold texto-principal")
        ui.label(datos["intervalo"]).classes("biseccion-numero texto-principal")
        if datos["muestra"]:
            ui.label(datos["muestra"]).classes("biseccion-numero text-sm texto-secundario")
        ui.label(candidato["mensaje"]).classes("text-sm texto-secundario")
        if datos["seleccionable"]:
            ui.button(f"Cargar intervalo {indice}", color=None,
                      on_click=lambda: panel.seleccionar(respuesta, candidato)).classes(
                          "boton-discreto").props("ripple=false")
