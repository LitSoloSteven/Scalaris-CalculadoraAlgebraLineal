"""Coordinación acotada de cálculos reales retenidos por pruebas de vigencia."""
import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace

from nicegui import run
from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante


@asynccontextmanager
async def retener_calculo(monkeypatch, vista, boton):
    """Retiene solo el determinante; libera y espera su tarea incluso si falla una aserción."""
    preparado, terminar = asyncio.Event(), asyncio.Event()
    trabajador_original = run.io_bound

    async def trabajador(funcion, *argumentos, **opciones):
        """Deja pasar otros trabajos de la página sin confundirlos con el cálculo retenido."""
        if funcion is not ControladorDeterminante.procesar_captura:
            return await trabajador_original(funcion, *argumentos, **opciones)
        preparado.set()
        await terminar.wait()
        return funcion(*argumentos, **opciones)

    monkeypatch.setattr(run, 'io_bound', trabajador)
    tarea = asyncio.create_task(vista.calcular(SimpleNamespace(sender=boton)))
    try:
        await asyncio.wait_for(preparado.wait(), timeout=2)
        assert not tarea.done()
        yield tarea
    finally:
        terminar.set()
        await asyncio.wait_for(tarea, timeout=2)
