"""Módulo compartido para lanzar corrutinas asociadas a clientes NiceGUI."""
from __future__ import annotations

import asyncio
from typing import Any, Coroutine


def lanzar_tarea(cliente: Any, corrutina: Coroutine[Any, Any, Any]) -> asyncio.Task:
    """Crea una tarea async que entra al contexto del cliente antes de ejecutar la corrutina.

    Si el cliente no está disponible o fue eliminado, ejecuta la corrutina directamente.
    Garantiza el cierre seguro de la corrutina en caso de cancelación o fallo al crear la tarea.
    """
    async def ejecutor():
        if cliente is not None and not getattr(cliente, "is_deleted", False):
            with cliente:
                return await corrutina
        return await corrutina

    ejec = ejecutor()
    try:
        tarea = asyncio.create_task(ejec)
        tarea.add_done_callback(lambda _: corrutina.close())
        return tarea
    except Exception:
        ejec.close()
        corrutina.close()
        raise
