"""Montaje real de los paneles vectoriales desde sus consumidores de vista."""
import pytest
from nicegui import ui

from src.frontend.vistas.operaciones_vectores.vista_operaciones_vectores import VistaOperacionesVectores
from src.frontend.vistas.operaciones_vectores import controles


@pytest.mark.parametrize("metodo,nombre_panel", [
    ("construir_suma_resta", "panel_suma_resta"),
    ("construir_escalar", "panel_escalar"),
])
def test_consumidor_monta_un_panel_vectorial_con_celdas_reales(metodo, nombre_panel):
    """El contenido específico usa el método vigente del componente de captura."""
    vista = VistaOperacionesVectores()
    contenedor = ui.column()
    try:
        with contenedor:
            getattr(controles, metodo)(vista)
        panel = getattr(vista, nombre_panel)
        assert panel.contenedor is not None
        assert panel.contenedor in list(contenedor.descendants())
        entradas = [elemento for elemento in panel.contenedor.descendants() if isinstance(elemento, ui.input)]
        assert len(entradas) == panel.dimension
        assert [entrada._props["data-geometria-indice"] for entrada in entradas] == ["0", "1", "2"]
    finally:
        contenedor.delete()
