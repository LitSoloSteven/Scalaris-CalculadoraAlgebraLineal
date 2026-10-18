"""Limpieza del botón tardío y descarte de cancelaciones de otras consultas."""
import threading
from types import SimpleNamespace
from unittest.mock import Mock

from nicegui import ui

from src.frontend.componentes.glosa_espera import finalizar_envio, iniciar_temporizador_cancelar


def _preparar_espera(monkeypatch):
    temporizador = SimpleNamespace(cancel=Mock())
    capturados = []

    def registrar(intervalo, manejador, once):
        """Captura el manejador y el argumento externo de ejecución única de NiceGUI."""
        capturados.append((intervalo, manejador, once))
        return temporizador

    monkeypatch.setattr(ui, "timer", registrar)
    instancia = SimpleNamespace(area_chat=ui.column(), _contador_solicitudes=1,
                                _esta_enviando=True, _desplazar_al_final=Mock(),
                                _renderizar_sugerencias_laterales=Mock(), campo_entrada=Mock())
    escritura = ui.row()
    indicadores = iniciar_temporizador_cancelar(instancia, 1, threading.Event(), escritura)
    return instancia, indicadores, capturados, temporizador


def test_finalizar_retira_boton_creado_despues_de_la_programacion(monkeypatch):
    """La referencia tardía permanece disponible al concluir la consulta."""
    instancia, indicadores, manejadores, temporizador = _preparar_espera(monkeypatch)
    try:
        assert indicadores.boton_cancelar is None
        assert manejadores[0][0] == 5 and manejadores[0][2] is True
        manejadores[0][1]()
        boton = indicadores.boton_cancelar
        assert boton is not None and not boton.is_deleted
        finalizar_envio(instancia, indicadores)
        assert boton.is_deleted and indicadores.escritura.is_deleted
        temporizador.cancel.assert_called_once_with()
        assert instancia._esta_enviando is False
        instancia.campo_entrada.enable.assert_called_once_with()
    finally:
        instancia.area_chat.delete()


def test_manejador_obsoleto_no_monta_cancelacion(monkeypatch):
    """Una nueva consulta no recibe el botón del temporizador anterior."""
    instancia, indicadores, manejadores, _ = _preparar_espera(monkeypatch)
    try:
        instancia._contador_solicitudes = 2
        manejadores[0][1]()
        assert indicadores.boton_cancelar is None
        instancia._desplazar_al_final.assert_not_called()
    finally:
        finalizar_envio(instancia, indicadores)
        instancia.area_chat.delete()
