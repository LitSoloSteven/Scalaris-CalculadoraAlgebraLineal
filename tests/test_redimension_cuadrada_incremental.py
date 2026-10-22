"""Conservación del interior y recuperación del borde de las matrices cuadradas."""
import asyncio
from unittest.mock import AsyncMock
import pytest
from nicegui import ui, Client
from src.frontend.componentes.panel_matriz_cuadrada import PanelMatrizCuadrada


def test_cincuenta_por_cincuenta_solo_recrea_el_borde(monkeypatch):
    """El interior de 49×49 conserva sus elementos al aumentar y quitar el borde."""
    monkeypatch.setattr(ui, 'run_javascript', AsyncMock())

    async def comprobar():
        """Comprueba identidades DOM y valor exacto en la dimensión máxima."""
        cliente = Client(ui.page('/prueba_borde'))
        try:
            with cliente:
                panel = PanelMatrizCuadrada(49)
                panel.construir_contenedor()
                interior = panel.celdas[0][0]
                interior.set_value('1/1001')
                await panel._redimensionar_asincrono(1)
                assert panel.dimension == 50 and panel.celdas[0][0] is interior
                assert sum(len(fila) for fila in panel.celdas) == 2500
                assert not panel.boton_aumentar.enabled
                await panel._redimensionar_asincrono(-1)
                assert panel.celdas[0][0] is interior and interior.value == '1/1001'
                assert panel.boton_aumentar.enabled
        finally:
            cliente.delete()
    asyncio.run(comprobar())


def test_una_fila_ausente_en_el_registro_obliga_a_reconstruir(monkeypatch):
    """La recuperación comprueba también la cantidad de filas de celdas almacenadas."""
    monkeypatch.setattr(ui, 'run_javascript', AsyncMock())

    async def comprobar():
        """Simula un registro parcial y conserva la captura mediante el respaldo completo."""
        cliente = Client(ui.page('/prueba_registro_incompleto'))
        try:
            with cliente:
                panel = PanelMatrizCuadrada(2)
                panel.construir_contenedor()
                panel.celdas[0][0].set_value('3/11')
                panel.celdas.pop()
                await panel._redimensionar_asincrono(1)
                assert panel.dimension == len(panel.celdas) == len(panel.filas_interfaz) == 3
                assert all(len(fila) == 3 for fila in panel.celdas)
                assert panel.celdas[0][0].value == '3/11'
        finally:
            cliente.delete()
    asyncio.run(comprobar())


def test_fallo_creando_borde_rehabilita_botones_y_permite_reintentar(monkeypatch):
    """Una reconstrucción parcial fallida no deja bloqueado el panel ni borra su caché."""
    transporte = AsyncMock()
    monkeypatch.setattr(ui, 'run_javascript', transporte)

    async def comprobar():
        """Fuerza un fallo de creación y repara la captura en el siguiente cambio."""
        cliente = Client(ui.page('/prueba_fallo_borde'))
        try:
            with cliente:
                panel = PanelMatrizCuadrada(2)
                panel.construir_contenedor()
                panel.celdas[0][0].set_value('2/7')
                crear = panel._crear_celda_ui
                monkeypatch.setattr(panel, '_crear_celda_ui', lambda *_: (_ for _ in ()).throw(RuntimeError('fallo simulado')))
                with pytest.raises(RuntimeError):
                    await panel._redimensionar_asincrono(1)
                assert panel.boton_reducir.enabled and panel.boton_aumentar.enabled
                assert not panel._redimensionando
                assert 'restaurarCeldas' in transporte.call_args.args[0]
                monkeypatch.setattr(panel, '_crear_celda_ui', crear)
                await panel._redimensionar_asincrono(-1)
                assert panel.dimension == 2 and panel.celdas[0][0].value == '2/7'
        finally:
            cliente.delete()
    asyncio.run(comprobar())
