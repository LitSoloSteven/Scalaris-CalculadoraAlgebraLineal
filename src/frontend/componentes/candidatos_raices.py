"""Lista accesible de registros de exploración con carga explícita de intervalos aptos."""
from nicegui import ui
from collections.abc import Callable
from dataclasses import dataclass

from src.frontend.controladores.exploracion_raices import detalles_contacto, presentar_candidato, texto_consumo_exploracion


@dataclass(frozen=True)
class PresentacionCandidatos:
    """Textos y clase numérica del consumidor, sin conocer su vista concreta."""

    indicacion: str
    clase_numero: str


def mostrar_candidatos(respuesta: dict, seleccionar: Callable, presentacion: PresentacionCandidatos) -> None:
    """Compone avisos y candidatos; los registros no aptos solo permiten inspección textual."""
    for advertencia in respuesta["advertencias"]:
        ui.label(advertencia).classes("text-sm texto-secundario")
    ui.label(texto_consumo_exploracion(respuesta)).classes(
        f"{presentacion.clase_numero} texto-secundario")
    total = len(respuesta["candidatos"])
    if not total:
        ui.label("No se detectaron candidatos en este rango. Cambia el rango o ajusta el paso en Avanzado.").classes(
            "texto-secundario")
        return
    ui.label(f"{total} candidato" + ("s" if total != 1 else "")).classes("font-semibold texto-principal")
    ui.label(presentacion.indicacion).classes(
        "text-sm texto-secundario")
    with ui.row().classes("w-full items-start gap-2"):
        for indice, candidato in enumerate(respuesta["candidatos"], 1):
            _mostrar_candidato(respuesta, (indice, candidato), seleccionar, presentacion)


def _mostrar_candidato(respuesta: dict, registro: tuple, seleccionar: Callable, presentacion: PresentacionCandidatos) -> None:
    indice, candidato = registro
    datos = presentar_candidato(candidato)
    titulo = f"{indice}. {datos['etiqueta']} · {datos['intervalo']}"
    with ui.column().classes("min-w-0 max-w-full gap-1"):
        if datos["seleccionable"]:
            ui.button(f"Cargar intervalo {titulo}", color=None,
                      on_click=lambda: seleccionar(respuesta, candidato)).classes(
                          f"boton-discreto {presentacion.clase_numero}").props("ripple=false")
        with ui.expansion("Detalles" if datos["seleccionable"] else titulo).classes("min-w-0 max-w-full"):
            _mostrar_evidencia(candidato, datos, presentacion)


def _mostrar_evidencia(candidato: dict, datos: dict, presentacion: PresentacionCandidatos) -> None:
    if datos["muestra"]:
        ui.label(datos["muestra"]).classes(f"{presentacion.clase_numero} text-sm texto-secundario")
    ui.label(candidato["mensaje"]).classes("text-sm texto-secundario")
    for detalle in detalles_contacto(candidato):
        ui.label(detalle).classes(f"{presentacion.clase_numero} text-sm texto-secundario")
