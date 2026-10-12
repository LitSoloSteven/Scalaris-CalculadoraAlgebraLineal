"""Invocación real de la salida vectorial antes de reducir su dimensión."""
import asyncio
from unittest.mock import Mock
import pytest
from nicegui import ui

from src.frontend.componentes import vector_capture
from src.frontend.vistas.geometria._panel_vectores import PanelVectoresGeometria
from tests.comun_animaciones_cliente import observar_invocaciones_cliente


@pytest.fixture
def panel_vectorial_montado():
    """Proporciona un contenedor real y garantiza su eliminación tras el caso."""
    panel = vector_capture.VectorCapturePanel("prueba")
    panel.container = ui.column()
    try:
        yield panel
    finally:
        panel.container.delete()


def test_reduccion_vectorial_espera_salida_antes_de_purgar_y_renderizar(monkeypatch, panel_vectorial_montado):
    """La salida se ejecuta sobre el índice anterior y luego se actualiza el panel."""
    panel = panel_vectorial_montado
    panel.vectors = {"u": {"cache": {0: "1", 1: "2", 2: "3"}}}
    codigos = []
    estados_salida = []

    async def registrar_salida(codigo):
        codigos.append(codigo)
        estados_salida.append((panel.dim, dict(panel.vectors["u"]["cache"])))

    monkeypatch.setattr(vector_capture.ui, "run_javascript", registrar_salida)
    panel.render_vector_grid = Mock()
    panel.on_data_change = Mock()
    asyncio.run(panel.adjust_dimension(-1))
    assert len(codigos) == 1
    assert "window.animateVectorDimensionRemoval" not in codigos[0]
    assert "window.scalaris?.cuadricula?.animarSalidaCeldas" in codigos[0]
    assert "data-geometria-indice='2'" in codigos[0]
    assert estados_salida == [(3, {0: "1", 1: "2", 2: "3"})]
    assert observar_invocaciones_cliente(codigos) == [{
        "selectores": [f"#{panel.container.html_id} input[data-geometria-indice='2']"], "duraciones": [140], "inyeccion": False,
    }]
    assert panel.dim == 2
    assert panel.vectors["u"]["cache"] == {0: "1", 1: "2"}
    panel.render_vector_grid.assert_called_once_with("u")
    panel.on_data_change.assert_called_once_with()


@pytest.mark.parametrize("tipo_panel", [vector_capture.VectorCapturePanel, PanelVectoresGeometria])
def test_reducir_un_panel_no_anima_ni_altera_otro(monkeypatch, tipo_panel):
    """La salida respeta contenedores independientes aunque compartan nombres e índices."""
    contenedor = ui.column()
    try:
        with contenedor:
            primero = tipo_panel("primero", max_vectors=2)
            primero.build(ui.column())
            segundo = tipo_panel("segundo", max_vectors=2)
            segundo.build(ui.column())
        ubicaciones = _ubicaciones_celdas([primero, segundo])
        codigos = []

        async def registrar_salida(codigo):
            codigos.append({"codigo": codigo, "ubicaciones": ubicaciones})

        monkeypatch.setattr(vector_capture.ui, "run_javascript", registrar_salida)
        asyncio.run(primero.adjust_dimension(-1))
        observacion = observar_invocaciones_cliente(codigos)[0]
        assert observacion["animaciones_por_celda"] == [0, 0, 1, 0, 0, 0]
        assert observacion["duraciones"] == [140]
        assert primero.dim == 2
        assert segundo.dim == 3
        assert len(list(segundo.vectors["u"]["ui_container"].descendants())) > 0
    finally:
        contenedor.delete()


def _ubicaciones_celdas(paneles):
    ubicaciones = []
    for panel in paneles:
        entradas = [elemento for elemento in panel.container.descendants() if isinstance(elemento, ui.input)]
        ubicaciones.extend({"panel": panel.container.html_id, "indice": entrada._props["data-geometria-indice"]}
                           for entrada in entradas)
    return ubicaciones
