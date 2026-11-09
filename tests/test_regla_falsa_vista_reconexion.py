"""Mensajes vigentes tras revocación y nombres distinguibles de los recientes."""
import asyncio

import pytest
from nicegui import run, ui

from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


@pytest.mark.parametrize("pendiente", [False, True])
def test_reconexion_retira_mensajes_anteriores_y_permite_recalcular(monkeypatch, pendiente):
    """Reconectar no conserva el título de éxito ni la carga de un cálculo revocado."""
    async def comprobar(vista):
        """Retiene o completa un cálculo antes de cerrar y reabrir los controles."""
        vista.cargar_captura(captura_regla_falsa())
        inicio, liberar = asyncio.Event(), asyncio.Event()

        async def trabajar(calcular, captura):
            """Espera una señal antes de ejecutar el motor real."""
            inicio.set()
            await liberar.wait()
            return calcular(captura)

        if pendiente:
            monkeypatch.setattr(run, "io_bound", trabajar)
            tarea = asyncio.create_task(vista.resolver())
            await asyncio.wait_for(inicio.wait(), 2)
        else:
            await vista.resolver()
        vista.cerrar()
        vista.reabrir()
        if pendiente:
            liberar.set()
            await tarea
        assert vista.ultimo_resultado is None and not vista.ocupado
        assert "Calcula de nuevo" in vista.estado.text
        assert "Calculando" not in vista.estado.text and "Convergió" not in vista.estado.text
    ejecutar_escenario(monkeypatch, comprobar)


def test_cancelacion_anuncia_ausencia_de_resultado(monkeypatch):
    """Cancelar la espera restituye el estado orientativo además del botón."""
    async def comprobar(vista):
        """Cancela el transporte pendiente y verifica que la carga no siga anunciándose."""
        inicio = asyncio.Event()

        async def esperar(calcular, captura):
            """Mantiene pendiente el transporte hasta recibir la cancelación."""
            inicio.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(run, "io_bound", esperar)
        vista.cargar_captura(captura_regla_falsa())
        tarea = asyncio.create_task(vista.resolver())
        await asyncio.wait_for(inicio.wait(), 2)
        tarea.cancel()
        await tarea
        assert vista.boton_resolver.enabled and "Calcula de nuevo" in vista.estado.text
    ejecutar_escenario(monkeypatch, comprobar)


def test_recientes_identifican_ejercicio_y_configuracion(monkeypatch):
    """Dos convergencias del mismo ejercicio tienen nombres accesibles distinguibles por tolerancia."""
    async def comprobar(vista):
        """Calcula con dos tolerancias y compara las etiquetas de los botones del historial."""
        for tolerancia in ("1e-6", "1e-9"):
            vista.cargar_captura(captura_regla_falsa(tolerancia=tolerancia))
            await vista.resolver()
        nombres = [elemento.text for elemento in vista.recientes.descendants() if isinstance(elemento, ui.button)]
        assert len(set(nombres)) == 2
        assert "x^2-2" in nombres[0] and "1e-9" in nombres[0] and "radianes" in nombres[0]
        assert "1e-6" in nombres[1]
    ejecutar_escenario(monkeypatch, comprobar)
