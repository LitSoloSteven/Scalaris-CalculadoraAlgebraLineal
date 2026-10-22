"""Captura accesible compartida por las presentaciones de Glosa."""
from dataclasses import dataclass
from typing import Any

from nicegui import ui
from src.ai.constantes import MAXIMO_CARACTERES_MENSAJE


@dataclass(frozen=True)
class EstiloEntradaGlosa:
    """Agrupa las clases y textos propios de cada presentación de la entrada."""

    clases_contenedor: str
    clases_campo: str
    clases_boton: str
    texto_ayuda: str
    etiqueta_envio: str


def construir_entrada_glosa(instancia: Any, estilo: EstiloEntradaGlosa) -> None:
    """Construye el campo y vincula Enter y el botón al mismo envío del panel."""
    with ui.row().classes(estilo.clases_contenedor):
        instancia.campo_entrada = ui.textarea(placeholder=estilo.texto_ayuda).classes(
            estilo.clases_campo
        ).props(f"borderless autogrow maxlength={MAXIMO_CARACTERES_MENSAJE}")
        instancia.campo_entrada.on("keydown.enter.prevent.exact", instancia.enviar_mensaje)
        ui.button(icon="send", on_click=instancia.enviar_mensaje, color=None).classes(
            estilo.clases_boton
        ).props(f'ripple=false aria-label="{estilo.etiqueta_envio}"').tooltip("Enviar")
