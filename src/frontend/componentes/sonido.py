"""Emisión de señales sonoras y notificaciones en el cliente activo."""
import json
from typing import Any

from nicegui import context, ui

_SONIDOS = frozenset({'accion', 'navegacion', 'apertura', 'cierre', 'exito', 'aviso', 'error'})
_POR_TIPO = {'positive': 'exito', 'negative': 'error', 'warning': 'aviso'}


def emitir_sonido(nombre: str) -> bool:
    """Envía una señal conocida al cliente conectado; devuelve si pudo enviarla, sin esperar audio."""
    if nombre not in _SONIDOS:
        return False
    try:
        cliente = context.client
        if cliente.is_deleted or not cliente.has_socket_connection:
            return False
        cliente.run_javascript(f'window.scalaris?.sonido?.reproducir({json.dumps(nombre)});')
    except RuntimeError:
        return False
    return True


def notificar(mensaje: str, **opciones: Any) -> Any:
    """Notifica con las opciones originales y añade una señal según el tipo; conserva el retorno de NiceGUI."""
    aviso = ui.notify(mensaje, **opciones)
    emitir_sonido(_POR_TIPO.get(opciones.get('type'), 'aviso'))
    return aviso
