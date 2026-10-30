"""Contrato de revelado único y seguro en ambas presentaciones de Glosa."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import ui
from nicegui.observables import ObservableDict

from src.ai.respuestas import ResultadoIA, TipoErrorIA
from src.frontend.componentes.glosa_envio import EnvioGlosaMixin
from src.frontend.componentes.glosa_bitacora import _renderizar_mensaje_lateral
from src.frontend.componentes.panel_ia_clasico import renderizar_mensaje_clasico
from tests.comun_clientes import PanelIASimulado


@pytest.mark.parametrize("lateral", [False, True])
def test_ambas_presentaciones_consumen_marca_y_conservan_escape(monkeypatch, lateral):
    """Solo el primer montaje se marca, y pre conserva el contenido hostil escapado."""
    monkeypatch.setattr('src.frontend.componentes.glosa_bitacora.sugerencias_activas', lambda: False)
    mensaje = {"texto": 'Texto```<script>alert(1)</script>```Final', "animar": True}
    contenedor = ui.column()
    instancia = SimpleNamespace()
    try:
        with contenedor:
            if lateral:
                _renderizar_mensaje_lateral(instancia, mensaje, True)
                _renderizar_mensaje_lateral(instancia, mensaje, True)
            else:
                renderizar_mensaje_clasico(mensaje)
                renderizar_mensaje_clasico(mensaje)
        contenidos = [elemento for elemento in contenedor.descendants() if isinstance(elemento, ui.html)]
        assert len(contenidos) == 2
        assert 'data-escritura-pendiente' in contenidos[0]._props
        assert 'data-escritura-pendiente' not in contenidos[1]._props
        assert mensaje['animar'] is False
        assert '<pre class="glosa-pre"><code>&lt;script&gt;' in contenidos[0].content
        assert '<script>' not in contenidos[0].content
    finally:
        contenedor.delete()


@pytest.mark.parametrize("exito", [True, False])
def test_solo_respuestas_exitosas_solicitan_revelado(monkeypatch, exito):
    """El flujo de resultados conserva errores inmediatos y anima solo respuestas válidas."""
    monkeypatch.setattr('src.frontend.componentes.glosa_envio.banderas.panel_lateral_habilitado', lambda: False)
    instancia = SimpleNamespace(historial_chat=[], area_chat=ui.column(),
                                _renderizar_mensaje=Mock(), _desplazar_al_final=Mock())
    resultado = ResultadoIA(exito, 'Respuesta', None if exito else TipoErrorIA.SERVICIO)
    try:
        EnvioGlosaMixin._procesar_resultado(instancia, resultado)
        mensaje = instancia.historial_chat[-1]
        assert mensaje.get('animar', False) is exito
        assert mensaje['error'] is not exito
        instancia._renderizar_mensaje.assert_called_once()
    finally:
        instancia.area_chat.delete()


@pytest.mark.parametrize("lateral", [False, True])
def test_reconstruir_almacen_observable_no_repite_revelado(monkeypatch, lateral):
    """La marca se consume en el objeto persistido por NiceGUI, también tras reconstruir."""
    monkeypatch.setattr('src.frontend.banderas.panel_lateral_habilitado', lambda: lateral)
    monkeypatch.setattr('src.frontend.componentes.glosa_bitacora.sugerencias_activas', lambda: False)
    almacen = ObservableDict({})
    panel = PanelIASimulado(almacen=almacen)
    panel.area_chat = ui.column()
    panel._desplazar_al_final = Mock()
    try:
        panel._procesar_resultado(ResultadoIA(True, 'Respuesta de prueba'))
        assert almacen['ia_historial_chat'][-1]['animar'] is False
        contenidos = [elemento for elemento in panel.area_chat.descendants() if isinstance(elemento, ui.html)]
        assert 'data-escritura-pendiente' in contenidos[0]._props
        panel.renderizar_chat()
        contenidos = [elemento for elemento in panel.area_chat.descendants() if isinstance(elemento, ui.html)]
        assert 'data-escritura-pendiente' not in contenidos[0]._props
    finally:
        panel.area_chat.delete()
