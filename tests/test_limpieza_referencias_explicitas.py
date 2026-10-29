"""Comprueba la selección y restauración de las capturas que se limpian."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from nicegui import ui

from src.frontend.componentes.limpieza_captura import LimpiezaCaptura


def test_limpieza_envia_referencias_y_restaura_despues_de_vaciar(monkeypatch):
    """La ejecución transmite solo las referencias vigentes y restaura al final."""
    eventos = []
    captura = SimpleNamespace(limpiar_todo=lambda: eventos.append('vaciar'))
    campos = [SimpleNamespace(id=12, is_deleted=False),
              SimpleNamespace(id=13, is_deleted=True)]
    async def ejecutar(codigo, **opciones):
        """Registra el código enviado al cliente sin abrir una conexión."""
        eventos.append(codigo)
    monkeypatch.setattr(ui, 'run_javascript', ejecutar)
    asyncio.run(LimpiezaCaptura(captura, lambda: True, lambda: campos).ejecutar())
    assert 'animarRecoleccionBasura([12])' in eventos[0]
    assert eventos[1] == 'vaciar'
    assert 'terminarRecoleccionBasura' in eventos[2]


def test_limpieza_restaura_si_la_animacion_agota_su_plazo(monkeypatch):
    """Un timeout no impide vaciar ni solicitar la restauración visual."""
    captura = SimpleNamespace(limpiar_todo=Mock())
    llamada = AsyncMock(side_effect=[TimeoutError(), None])
    monkeypatch.setattr(ui, 'run_javascript', llamada)
    control = LimpiezaCaptura(captura, lambda: True, lambda: [])
    asyncio.run(control.ejecutar())
    captura.limpiar_todo.assert_called_once()
    assert llamada.await_count == 2
    assert 'terminarRecoleccionBasura' in llamada.await_args.args[0]
    assert not control._limpiando


def test_cancelacion_de_restauracion_libera_el_control(monkeypatch):
    """La cancelación del transporte no deja bloqueada la captura."""
    captura = SimpleNamespace(limpiar_todo=Mock())
    llamada = AsyncMock(side_effect=[None, asyncio.CancelledError()])
    monkeypatch.setattr(ui, 'run_javascript', llamada)
    control = LimpiezaCaptura(captura, lambda: True, lambda: [])
    liberar = Mock()
    monkeypatch.setattr(control, '_liberar_captura', liberar)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(control.ejecutar())
    assert not control._limpiando
    liberar.assert_called_once()
