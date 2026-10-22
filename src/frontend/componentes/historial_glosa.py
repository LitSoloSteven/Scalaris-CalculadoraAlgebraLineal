"""Actualización íntegra del historial con una sola publicación observable."""
from typing import Any
from src.frontend.constantes import MAXIMO_HISTORIAL


def incorporar_mensaje(historial: list[dict[str, Any]], mensaje: dict[str, Any]) -> list[dict[str, Any]]:
    """Devuelve los últimos mensajes incluyendo el recibido, sin modificar la lista original."""
    return [*historial, mensaje][-MAXIMO_HISTORIAL:]
