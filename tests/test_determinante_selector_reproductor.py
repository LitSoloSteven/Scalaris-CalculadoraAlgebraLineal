"""Eleccion de metodo, reproductor e invalidacion con controles reales NiceGUI."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend.vistas.operaciones_matrices._presentacion_determinante import adaptar_traza
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_calculo_determinante import retener_calculo


def _boton_calcular(cliente):
    return next(elemento for elemento in cliente.elements.values()
                if isinstance(elemento, ui.button) and elemento.text == "Calcular determinante")


@pytest.mark.parametrize("metodo", ["laplace", "lu"])
def test_calculo_renderiza_metodo_y_limpia_resultado_al_editar(monkeypatch, metodo):
    """La seleccion llega al backend y los datos editados retiran pasos y contexto anterior."""
    async def comprobar(vista, cliente):
        """Calcula y recorre todos los pasos antes de invalidar la captura."""
        vista.panel_matriz.cargar_matriz([["1", "2", "3"], ["0", "0", "4"], ["5", "6", "7"]])
        vista.metodos_determinante.set_value(metodo)
        await vista.recomendacion.tarea
        assert vista.metodos_determinante.value == metodo
        await vista.calcular(SimpleNamespace(sender=_boton_calcular(cliente)))
        assert vista.ultimo_resultado["metodo"] == metodo
        assert vista.ultimo_resultado["determinante"] == 16
        reproductor = vista.reproductor_pasos
        assert reproductor is not None
        for paso in reproductor.pasos:
            reproductor.ir_a(paso.indice)
        assert vista.obtener_contexto_ia().resultado["metodo"] == metodo
        assert "16" in vista.panel_ia._recopilar_contexto()
        limpiar_foco = Mock(wraps=vista.panel_ia.limpiar_foco_explicacion)
        monkeypatch.setattr(vista.panel_ia, "limpiar_foco_explicacion", limpiar_foco)
        reproductor.temporizador.active = True
        vista._invalidar_resultado()
        limpiar_foco.assert_called_once()
        assert vista.ultimo_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert vista.reproductor_pasos is None
        assert reproductor.temporizador is None
    asyncio.run(construir_pagina(monkeypatch, "determinantes", comprobar))


def test_cambiar_metodo_descarta_calculo_pendiente(monkeypatch):
    """Un cambio del selector durante el trabajo invalida la respuesta del metodo anterior."""
    async def comprobar(vista, cliente):
        """Retiene el trabajador hasta despues de cambiar la seleccion de metodo."""
        assert vista.metodos_determinante.value == "lu"
        mostrar = Mock()
        monkeypatch.setattr(vista, "_mostrar_resultado", mostrar)
        boton = _boton_calcular(cliente)
        async with retener_calculo(monkeypatch, vista, boton):
            assert boton._props['loading'] == 'true'
            vista.metodos_determinante.set_value("laplace")
        mostrar.assert_not_called()
        assert vista.ultimo_resultado is None
        assert boton._props['loading'] == 'false'
        assert vista.obtener_contexto_ia().resultado is None
    asyncio.run(construir_pagina(monkeypatch, "determinantes", comprobar))


def test_adaptador_conserva_datos_backend_sin_recalcular():
    """El adaptador transporta el cuerpo matematico sin alterarlo."""
    cuerpo = {"tipo": "menor", "descripcion": "Menor", "explicacion": "Eliminar fila 2", "detalle_latex": "16"}
    pasos, grupos = adaptar_traza({"traza": [cuerpo]})
    assert pasos[0].cuerpo is cuerpo
    assert pasos[0].meta_explicar["detalle"]["formula"] == "16"
    assert grupos[0].indices_pasos == (0,)
