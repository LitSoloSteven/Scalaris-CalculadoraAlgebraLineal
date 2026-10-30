"""Reinicio de esperas y preferencia de velocidad al reconstruir el reproductor."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

from nicegui import Client, core, ui

from src.frontend.componentes.reproductor_pasos import PasoReproductor, ReproductorPasos
from src.frontend.componentes.reproductor_pasos.temporizacion import reiniciar_espera


def test_reinicio_retira_espera_anterior_y_no_avanza_inmediatamente(monkeypatch):
    """La espera anterior se cancela y la nueva empieza con el intervalo completo."""
    anterior = Mock(is_deleted=False, interval=15)
    tarjeta = Mock(is_deleted=False)
    tarjeta.__enter__ = Mock()
    tarjeta.__exit__ = Mock()
    reproductor = SimpleNamespace(temporizador=anterior, tarjeta=tarjeta, _avanzar=Mock())
    crear = Mock(return_value=SimpleNamespace())
    monkeypatch.setattr(ui, "timer", crear)
    reiniciar_espera(reproductor)
    anterior.delete.assert_called_once()
    assert anterior.active is False
    crear.assert_called_once_with(15, reproductor._avanzar, active=True, immediate=False)
    assert reproductor.temporizador is crear.return_value


def test_reconstruccion_conserva_velocidad_y_reinicia_cambios_activos(monkeypatch):
    """Selector e intervalo coinciden después de reconstruir y de navegar durante reproducción."""
    async def comprobar():
        """Ejercita temporizadores reales sin esperar los segundos de lectura."""
        monkeypatch.setattr(core, "script_mode", False)
        monkeypatch.setattr(ui, "run_javascript", lambda codigo: None)
        cliente = Client(ui.page("/prueba_espera"))
        try:
            with cliente:
                pasos = [PasoReproductor(0, "inicial", "Inicio", "a" * 100),
                         PasoReproductor(1, "final", "Fin", "a" * 1000)]
                reproductor = ReproductorPasos(pasos, (), lambda paso, destino: None, "espera")
                reproductor.velocidad = "Lenta"
                reproductor.construir()
                selector = next(elemento for elemento in reproductor.tarjeta.descendants() if isinstance(elemento, ui.select))
                assert selector.value == "Lenta" and reproductor.temporizador.interval == 14.4
                reproductor._alternar_reproduccion()
                anterior = reproductor.temporizador
                reproductor.ir_a(1)
                assert anterior.is_deleted and reproductor.temporizador.active
                assert reproductor.temporizador.interval == 24
                assert reproductor.temporizador._immediate is False
                anterior = reproductor.temporizador
                reproductor._cambiar_velocidad(SimpleNamespace(value="Rápida"))
                assert anterior.is_deleted and reproductor.temporizador.interval == 9
                reproductor.detener()
        finally:
            cliente.delete()
    asyncio.run(comprobar())
