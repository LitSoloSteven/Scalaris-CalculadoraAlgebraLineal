"""Límites reales de coordinación bajo ediciones y desconexiones."""
import asyncio

import pytest
from nicegui import run

from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices


def test_cincuenta_ediciones_conservan_solo_el_ultimo_borrador(monkeypatch):
    """Cancelar esperas nunca libera la plaza del trabajador retenido."""
    async def comprobar():
        inicio, liberar = asyncio.Event(), asyncio.Event()
        llamadas = []
        async def trabajar(calcular, captura):
            llamadas.append(captura["valor"])
            inicio.set()
            await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        coordinador = CoordinadorTrabajosRaices(lambda captura: captura["valor"])
        antigua = asyncio.create_task(coordinador.ejecutar({"valor": 0}))
        await inicio.wait()
        for valor in range(1, 51):
            antigua.cancel()
            await asyncio.gather(antigua, return_exceptions=True)
            antigua = asyncio.create_task(coordinador.ejecutar({"valor": valor}))
            await asyncio.sleep(0)
            assert coordinador.activos == 1 and coordinador.pendientes == 1
        liberar.set()
        assert await antigua == 50
        await coordinador.esperar_cierre()
        assert llamadas == [0, 50]
        assert coordinador.activos == coordinador.pendientes == 0
    asyncio.run(comprobar())


def test_desconexion_retira_borrador_y_no_publica_resultado(monkeypatch):
    """Cerrar no ejecuta el borrador ni publica el trabajo de una sesión anterior."""
    async def comprobar():
        inicio, liberar = asyncio.Event(), asyncio.Event()
        llamadas = []
        async def trabajar(calcular, captura):
            llamadas.append(captura)
            inicio.set()
            await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        coordinador = CoordinadorTrabajosRaices(dict)
        primera = asyncio.create_task(coordinador.ejecutar({"valor": 0}))
        await inicio.wait()
        segunda = asyncio.create_task(coordinador.ejecutar({"valor": 1}))
        await asyncio.sleep(0)
        coordinador.cerrar()
        assert await segunda is None
        assert await coordinador.ejecutar({}) is None
        assert coordinador.activos == 1 and coordinador.pendientes == 0
        liberar.set()
        assert await primera is None
        await coordinador.esperar_cierre()
        assert len(llamadas) == 1
        coordinador.reabrir()
        assert await coordinador.ejecutar({"valor": 2}) == {"valor": 2}
    asyncio.run(comprobar())


def test_error_vigente_se_propaga_y_la_plaza_se_recupera(monkeypatch):
    """Una excepción no conserva una plaza ocupada ni oculta el fallo al consumidor."""
    async def comprobar():
        async def trabajar(calcular, captura):
            if captura.get("fallar"):
                raise ValueError("entrada rechazada")
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        coordinador = CoordinadorTrabajosRaices(dict)
        with pytest.raises(ValueError, match="entrada rechazada"):
            await coordinador.ejecutar({"fallar": True})
        assert await coordinador.ejecutar({"valor": 2}) == {"valor": 2}
        assert coordinador.activos == 0
    asyncio.run(comprobar())
