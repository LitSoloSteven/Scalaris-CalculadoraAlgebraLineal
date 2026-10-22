"""Módulo compartido para lanzar corrutinas asociadas a clientes NiceGUI."""
from __future__ import annotations

import asyncio
from typing import Any, Coroutine


def lanzar_tarea(cliente: Any, corrutina: Coroutine[Any, Any, Any]) -> asyncio.Task:
    """Devuelve una tarea en el contexto del cliente, o sin él si falta o fue eliminado.
    Cierra la corrutina al cancelar o al fallar la creación y propaga ese fallo."""
    async def ejecutor():
        """Ejecuta la tarea dentro del contexto del cliente que la solicitó."""
        if cliente is not None and not getattr(cliente, "is_deleted", False):
            with cliente:
                return await corrutina
        return await corrutina

    ejecucion = ejecutor()
    try:
        tarea = asyncio.create_task(ejecucion)
        tarea.add_done_callback(lambda _: corrutina.close())
        return tarea
    except Exception:
        ejecucion.close()
        corrutina.close()
        raise
