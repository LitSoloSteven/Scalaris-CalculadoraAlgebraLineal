"""Carga explícita de propuestas de dominio pertenecientes al resultado vigente."""
from nicegui import ui

from src.ai.huellas import calcular_huella
from src.frontend.controladores.formato_numerico_raices import texto_intervalo


def mostrar_sugerencias(vista, datos: dict) -> None:
    """Muestra únicamente propuestas verificadas del servicio, sin ejecutarlas al cargar."""
    for propuesta in datos.get("sugerencias", ()):
        with vista.contenedor_resultados:
            ui.label(propuesta["mensaje"]).classes("text-sm texto-secundario")
            ui.button(f"Cargar intervalo {texto_intervalo(propuesta['intervalo'])}", color=None,
                      on_click=lambda propuesta=propuesta: aplicar_sugerencia(vista, datos, propuesta)).classes(
                          "boton-discreto").props("ripple=false")


def aplicar_sugerencia(vista, datos: dict, propuesta: dict) -> None:
    """Carga extremos solo si la respuesta y su captura siguen vigentes y montadas."""
    if vista._cerrada or vista.ocupado or vista.contenedor_resultados.is_deleted:
        return
    if vista.ultimo_resultado is not datos["resultado"] or not any(
        propuesta is actual for actual in datos.get("sugerencias", ())
    ):
        return
    if vista._huella_resultado != calcular_huella(vista.capturar()):
        return
    inferior, superior = propuesta["intervalo"]
    vista.cargar_captura({"extremo_izquierdo": str(inferior), "extremo_derecho": str(superior)})
    vista.inferior.run_method("focus")
