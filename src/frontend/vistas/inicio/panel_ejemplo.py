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
    """Monta el ejemplo y lanza ValueError si el enlace no apunta a una ruta interna."""
    if (
        not enlace.startswith("/")
        or enlace.startswith(("//", "/\\"))
        or any(ord(caracter) < 32 for caracter in enlace)
    ):
        raise ValueError("El enlace del ejemplo debe apuntar a una ruta interna.")
    contenido = _leer_plantilla().substitute(enlace=escape(enlace, quote=True))
    # El sanitizador estricto del navegador suprime los controles del fragmento local.
    ui.html(contenido, sanitize=False).classes("inicio-ejemplo-contenedor")
