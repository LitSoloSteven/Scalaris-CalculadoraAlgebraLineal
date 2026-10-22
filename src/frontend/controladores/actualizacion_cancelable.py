"""Antirrebote cancelable para actualizaciones de presentación aún vigentes."""
import asyncio
from collections.abc import Awaitable, Callable


def cancelar_actualizacion(tarea: asyncio.Task | None) -> None:
    """Cancela una tarea pendiente sin afectar otras actualizaciones del cliente."""
    if tarea is not None and not tarea.done():
        tarea.cancel()


def programar_actualizacion(tarea: asyncio.Task | None, actualizar: Callable[[], Awaitable[None]],
                           sigue_vigente: Callable[[], bool], demora: float) -> asyncio.Task:
    """Sustituye la espera anterior y ejecuta el callback solo si conserva vigencia."""
    cancelar_actualizacion(tarea)
    return asyncio.create_task(_esperar_actualizacion(actualizar, sigue_vigente, demora))


async def _esperar_actualizacion(actualizar, sigue_vigente, demora: float) -> None:
    await asyncio.sleep(demora)
    if sigue_vigente():
        await actualizar()
