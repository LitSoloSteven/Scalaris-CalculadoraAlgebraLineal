"""Contexto de errores y acciones opcionales sobre una respuesta aún vigente."""
from nicegui import ui

from src.frontend.controladores.biseccion.presentacion_diagnostico import (
    detalles_diagnostico, texto_intervalo, texto_sugerencia,
)


def mostrar_avisos_diagnostico(vista, respuesta: dict) -> None:
    """Muestra datos del dominio y acciones explícitas que cargan campos sin resolver."""
    for etiqueta, valor in detalles_diagnostico(respuesta):
        ui.label(f"{etiqueta}: {valor}").classes("biseccion-numero text-sm texto-secundario")
    for sugerencia in respuesta.get("sugerencias", ()):
        ui.label(texto_sugerencia(sugerencia)).classes("text-sm texto-advertencia").props("role=status aria-live=polite")
        etiqueta = "Elegir ancho absoluto"
        if sugerencia["tipo"] == "intervalo_dominio":
            etiqueta = "Cargar intervalo " + texto_intervalo(sugerencia["intervalo"])
        ui.button(etiqueta, color=None,
                  on_click=lambda sugerencia=sugerencia: _aplicar_sugerencia(vista, respuesta, sugerencia)).classes(
                      "boton-discreto w-full whitespace-normal").props("ripple=false")


def _aplicar_sugerencia(vista, respuesta: dict, sugerencia: dict) -> None:
    if vista.ultimo_resultado is not respuesta or vista.contenedor_resultados.is_deleted or vista.ocupado:
        return
    if sugerencia["tipo"] == "intervalo_dominio":
        inferior, superior = sugerencia["intervalo"]
        vista.cargar_captura({"extremo_izquierdo": str(inferior), "extremo_derecho": str(superior)})
    elif sugerencia["tipo"] == "criterio_absoluto":
        parametro = vista.parametros_criterio["ancho"].value
        vista.cargar_captura({"criterio": {"tipo": "ancho", "parametro": parametro}})
