"""Coherencia del ejercicio vectorial con el foco y las señales de Glosa."""
import asyncio
from unittest.mock import Mock

import pytest

from tests.comun_clientes import PanelIASimulado
from tests.comun_vista_vectorial import vista_vectorial_montada, ejecutar_calculo_en_panel


def _adjuntar_panel(vista):
    panel = PanelIASimulado(vista)
    panel.programar_actualizacion_contexto = Mock()
    vista.panel_ia = panel
    return panel


def test_alternar_orientacion_notifica_y_omitir_vector_no_notifica(vista_vectorial_montada):
    """La orientación efectiva refresca el asistente exactamente una vez."""
    vista = vista_vectorial_montada
    panel = _adjuntar_panel(vista)
    vista.panel_suma_resta.alternar_orientacion("u")
    panel.programar_actualizacion_contexto.assert_called_once_with()
    assert "orient_mix" in vista.obtener_senales_ia().flags
    panel.programar_actualizacion_contexto.reset_mock()
    vista.panel_suma_resta.alternar_orientacion("ausente")
    panel.programar_actualizacion_contexto.assert_not_called()


@pytest.mark.parametrize("accion", ["limpiar", "pestana", "calcular"])
def test_procedimiento_retirado_no_conserva_foco_de_glosa(vista_vectorial_montada, accion):
    """Limpiar, cambiar pestaña y recalcular retiran el paso del ejercicio anterior."""
    vista = vista_vectorial_montada
    panel = _adjuntar_panel(vista)
    panel.explain_focus = {"index": 1, "total": 4, "kind": "componente", "op": "paso del ejercicio anterior"}
    if accion == "limpiar":
        vista.limpiar()
    elif accion == "pestana":
        vista.pestanas.set_value("escalar")
    else:
        asyncio.run(ejecutar_calculo_en_panel(vista))
    assert panel.explain_focus is None
    assert "paso del ejercicio anterior" not in panel._collect_context()


def test_contexto_incluye_escalar_y_opciones_de_resta(vista_vectorial_montada):
    """El contexto transporta las opciones que determinan el cálculo actual."""
    vista = vista_vectorial_montada
    vista.pestanas.set_value("escalar")
    vista.valor_escalar = "-3/7"
    assert vista.obtener_contexto_ia().entrada["opciones"] == {"escalar": "-3/7"}
    vista.pestanas.set_value("suma_resta")
    vista.operacion_suma_resta = "resta"
    vista.orientacion_estricta = True
    assert vista.obtener_contexto_ia().entrada["opciones"] == {"operacion": "resta", "estricto": True}
