"""Montaje y limpieza de componentes reales para las regresiones de vectores."""
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend.vistas.operaciones_vectores.vista_operaciones_vectores import VistaOperacionesVectores
from src.frontend.vistas.operaciones_vectores import controles


@pytest.fixture
def vista_vectorial_montada(monkeypatch):
    """Monta componentes reales y captura el JavaScript sin iniciar un navegador."""
    monkeypatch.setattr(ui, "run_javascript", Mock())
    contenedor = ui.column()
    vista = VistaOperacionesVectores()
    try:
        with contenedor:
            controles.construir_panel_izquierdo(vista)
            vista.panel_resultados = ui.column()
        yield vista
    finally:
        if vista.reproductor_pasos:
            vista.reproductor_pasos.detener()
        contenedor.delete()


async def ejecutar_calculo_en_panel(vista):
    """Proporciona al callback el contexto de cliente que aporta un evento NiceGUI."""
    with vista.panel_resultados:
        await vista.calcular()
