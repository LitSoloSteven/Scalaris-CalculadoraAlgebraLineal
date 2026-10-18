"""Presentación uniforme de estados de cálculo de modelos matriciales."""
import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any
from nicegui import ui

_REGISTRO = logging.getLogger(__name__)


def mostrar_estado(contenedor: Any, mensaje: str, estado: str = "VACIO") -> None:
    """Limpia un panel y publica un mensaje accesible de vacío, carga o error."""
    contenedor.clear()
    with contenedor:
        ui.label(mensaje).classes("texto-secundario break-words").props(
            'role="alert"' if estado == "ERROR" else 'role="status" aria-live="polite"'
        )


async def ejecutar_modelo(vista: Any, boton: Any, calcular: Callable[[], Awaitable[None]]) -> None:
    """Coordina carga y errores de un modelo; propaga cancelación y libera el botón."""
    if getattr(vista, "_calculando", False):
        return
    vista._calculando = True
    vista.ultimo_resultado = None
    boton.props("loading")
    mostrar_estado(vista.contenedor_resultados, "Calculando…", "CARGA")
    try:
        await asyncio.sleep(0)
        await calcular()
    except asyncio.CancelledError:
        mostrar_estado(vista.contenedor_resultados, "Cálculo cancelado. Vuelve a calcular.")
        raise
    except Exception:
        _REGISTRO.exception("No se pudo presentar el cálculo matricial")
        mostrar_estado(vista.contenedor_resultados, "Error inesperado. Revisa los datos e inténtalo de nuevo.", "ERROR")
    finally:
        vista._calculando = False
        boton.props(remove="loading")
