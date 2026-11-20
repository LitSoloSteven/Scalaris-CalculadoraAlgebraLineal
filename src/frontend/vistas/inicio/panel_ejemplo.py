"""Renderiza el ejemplo didáctico de la portada de Scalaris."""
from functools import cache
from html import escape
from pathlib import Path
from string import Template

from nicegui import ui

_RUTA_PLANTILLA = Path(__file__).resolve().parents[2] / "recursos" / "plantillas" / "ejemplos_inicio.html"


@cache
def _leer_plantilla() -> Template:
    return Template(_RUTA_PLANTILLA.read_text(encoding="utf-8"))


def renderizar_panel_ejemplo(enlace: str) -> None:
    """Monta el ejemplo inicial y el enlace interno a su módulo."""
    contenido = _leer_plantilla().substitute(enlace=escape(enlace, quote=True))
    ui.html(contenido).classes("inicio-ejemplo-contenedor")
