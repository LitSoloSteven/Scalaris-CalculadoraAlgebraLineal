"""Regresiones de la captura común de Glosa y la agrupación residual de pasos."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import Client, ui

from src.frontend.componentes.glosa_pie import construir_pie_lateral
from src.frontend.componentes.panel_ia_clasico import _construir_pie_clasico
from src.frontend.controladores.manejadores_pasos import _asociar_grupo_eliminacion, manejar_otro


@pytest.mark.parametrize('clasico', [False, True])
def test_entrada_glosa_conserva_texto_clases_y_envio(clasico):
    """Ambas presentaciones conservan nombres accesibles y comparten Enter y botón."""
    panel = SimpleNamespace(
        enviar_mensaje=Mock(), contexto_adjuntado=None, limpiar_contexto=Mock(),
        renderizar_pildora_contexto=Mock(), renderizar_capsula_foco_interfaz=Mock(),
        _renderizar_sugerencias_laterales=Mock(),
    )
    cliente = Client(ui.page('/captura_glosa_compartida'))
    try:
        with cliente:
            (_construir_pie_clasico if clasico else construir_pie_lateral)(panel)
        assert panel.campo_entrada._props['placeholder'] == ('Pregunta algo...' if clasico else 'Pregunta algo sobre tu ejercicio...')
        assert 'glosa-campo-entrada' in panel.campo_entrada._classes
        assert ('matriz-entrada' if clasico else 'glosa-entrada') in panel.campo_entrada._classes
        boton = next(elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.button))
        assert boton._props['aria-label'] == ('Enviar mensaje' if clasico else 'Enviar')
        assert 'glosa-boton-enviar' in boton._classes
        _comprobar_envio(panel, boton)
    finally:
        cliente.delete()


def _comprobar_envio(panel, boton):
    """Los eventos conservan el mismo manejador y las restricciones de Enter."""
    entrada = next(evento for evento in panel.campo_entrada._event_listeners.values() if evento.type.startswith('keydown.'))
    assert entrada.handler is panel.enviar_mensaje
    assert entrada.to_dict()['keys'] == ['enter'] and entrada.to_dict()['modifiers'] == ['prevent', 'exact']
    next(iter(boton._event_listeners.values())).handler(None)
    panel.enviar_mensaje.assert_called_once()


def test_grupo_residual_compartido_conserva_identidad_y_orden():
    """Ambos caminos reutilizan el grupo residual sin perder pasos ni su posición."""
    anterior = {'indices_pasos': [0]}
    grupos, estado = [anterior], {}
    assert _asociar_grupo_eliminacion(1, grupos, estado) == 1
    residual = estado['otro']
    assert manejar_otro(2, 'Otro paso', grupos, estado)[1] == 1
    assert estado['otro'] is residual
    assert grupos == [anterior, {'tipo': 'otros', 'titulo': 'Otras operaciones', 'indices_pasos': [1, 2]}]


@pytest.mark.parametrize('columna,normalizacion,esperado', [(True, True, 0), (False, True, 1)])
def test_otro_paso_respeta_precedencia_de_grupos(columna, normalizacion, esperado):
    """El grupo de columna precede al de normalización y ambos preceden al residual."""
    grupos = [{'indices_pasos': [0]}, {'indices_pasos': [1]}]
    estado = {'columna': grupos[0] if columna else None, 'normalizacion': grupos[1] if normalizacion else None}
    assert manejar_otro(3, 'Otro paso', grupos, estado)[1] == esperado
    assert grupos[esperado]['indices_pasos'][-1] == 3
    assert 'otro' not in estado
