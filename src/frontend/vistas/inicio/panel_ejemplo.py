"""Renderiza el ejemplo didáctico de la portada de Scalaris."""
from dataclasses import replace
from functools import cache
from html import escape
from pathlib import Path
from string import Template

from nicegui import ui

from src.frontend.controladores.inicio._modelo import EstadoPortada, estado_portada
from ._catalogo_ejemplos import obtener_ejemplo

_RUTA_PLANTILLA = Path(__file__).resolve().parents[2] / "recursos" / "plantillas" / "ejemplos_inicio.html"


@cache
def _leer_plantilla() -> Template:
    return Template(_RUTA_PLANTILLA.read_text(encoding="utf-8"))


def validar_enlace_interno(enlace: str) -> str:
    """Valida que enlace apunte a una ruta relativa del origen y lo devuelve.
    Lanza ValueError cuando el destino es externo, ambiguo o incluye controles."""
    if (
        not enlace.startswith("/")
        or enlace.startswith(("//", "/\\"))
        or any(ord(caracter) < 32 for caracter in enlace)
    ):
        raise ValueError("El enlace del ejemplo debe apuntar a una ruta interna.")
    return enlace


def construir_html_ejemplo(estado: EstadoPortada) -> str:
    """Compone y devuelve el HTML local del ejemplo para el estado recibido.
    Lanza ValueError si el enlace del estado no supera la validación interna."""
    enlace = validar_enlace_interno(estado.enlace)
    ejemplo = obtener_ejemplo(estado.clave)
    etiqueta_enlace = f"Ver módulo de {estado.titulo}"
    return _leer_plantilla().substitute(
        clave=escape(ejemplo.clave, quote=True),
        mensaje=escape(ejemplo.mensaje, quote=True),
        titulo=escape(estado.titulo),
        etiqueta_operacion=escape(ejemplo.etiqueta_operacion, quote=True),
        operacion=escape(ejemplo.operacion),
        etapas=ejemplo.etapas,
        enlace=escape(enlace, quote=True),
        etiqueta_enlace=escape(etiqueta_enlace, quote=True),
    )


def renderizar_panel_ejemplo(enlace: str, estado: EstadoPortada | None = None) -> ui.html:
    """Monta el ejemplo con enlace y estado opcional y devuelve su contenedor ui.html.
    Lanza ValueError si enlace no corresponde a una ruta interna válida."""
    estado_actual = replace(estado_portada() if estado is None else estado, enlace=enlace)
    contenido = construir_html_ejemplo(estado_actual)
    # El sanitizador estricto del navegador suprime los controles del fragmento local.
    return ui.html(contenido, sanitize=False).classes("inicio-ejemplo-contenedor")
