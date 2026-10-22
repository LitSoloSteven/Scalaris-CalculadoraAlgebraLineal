"""Invocación real de la salida vectorial antes de reducir su dimensión."""
import asyncio
from unittest.mock import Mock
import pytest
from nicegui import ui

from src.frontend.componentes import captura_vectores
from src.frontend.vistas.geometria._panel_vectores import PanelVectoresGeometria
from tests.comun_animaciones_cliente import observar_invocaciones_cliente


@pytest.fixture
def panel_vectorial_montado():
    """Proporciona un contenedor real y garantiza su eliminación tras el caso."""
    panel = captura_vectores.PanelCapturaVectores("prueba")
    panel.contenedor = ui.column()
    try:
        yield panel
    finally:
        panel.contenedor.delete()


def test_reduccion_vectorial_espera_salida_antes_de_purgar_y_renderizar(monkeypatch, panel_vectorial_montado):
    """La salida se ejecuta sobre el índice anterior y luego se actualiza el panel."""
    panel = panel_vectorial_montado
    panel.vectores = {"u": {"celdas": {0: "1", 1: "2", 2: "3"}}}
    codigos = []
    estados_salida = []

    async def registrar_salida(codigo):
        """Registra la salida de la celda para comprobar el orden de actualización."""
        codigos.append(codigo)
        estados_salida.append((panel.dimension, dict(panel.vectores["u"]["celdas"])))

    monkeypatch.setattr(captura_vectores.ui, "run_javascript", registrar_salida)
    panel.renderizar_cuadricula_vector = Mock()
    panel.al_cambiar_datos = Mock()
    asyncio.run(panel.ajustar_dimension(-1))
    assert len(codigos) == 1
    assert "window.animateVectorDimensionRemoval" not in codigos[0]
    assert "window.scalaris?.cuadricula?.animarSalidaCeldas" in codigos[0]
    assert "data-geometria-indice='2'" in codigos[0]
    assert estados_salida == [(3, {0: "1", 1: "2", 2: "3"})]
    assert observar_invocaciones_cliente(codigos) == [{
        "selectores": [f"#{panel.contenedor.html_id} input[data-geometria-indice='2']"], "duraciones": [140], "inyeccion": False,
    }]
    assert panel.dimension == 2
    assert panel.vectores["u"]["celdas"] == {0: "1", 1: "2"}
    panel.renderizar_cuadricula_vector.assert_called_once_with("u")
    panel.al_cambiar_datos.assert_called_once_with()


@pytest.mark.parametrize("tipo_panel", [captura_vectores.PanelCapturaVectores, PanelVectoresGeometria])
def test_reducir_un_panel_no_anima_ni_altera_otro(monkeypatch, tipo_panel):
    """La salida respeta contenedores independientes aunque compartan nombres e índices."""
    contenedor = ui.column()
    try:
        with contenedor:
            primero = tipo_panel("primero", opciones={"maximo_vectores": 2})
            primero.construir(ui.column())
            segundo = tipo_panel("segundo", opciones={"maximo_vectores": 2})
            segundo.construir(ui.column())
        ubicaciones = _ubicaciones_celdas([primero, segundo])
        codigos = []

        async def registrar_salida(codigo):
            """Registra la salida de la celda para comprobar el orden de actualización."""
            codigos.append({"codigo": codigo, "ubicaciones": ubicaciones})

        monkeypatch.setattr(captura_vectores.ui, "run_javascript", registrar_salida)
        asyncio.run(primero.ajustar_dimension(-1))
        observacion = observar_invocaciones_cliente(codigos)[0]
        assert observacion["animaciones_por_celda"] == [0, 0, 1, 0, 0, 0]
        assert observacion["duraciones"] == [140]
        assert primero.dimension == 2
        assert segundo.dimension == 3
        assert len(list(segundo.vectores["u"]["contenedor"].descendants())) > 0
    finally:
        contenedor.delete()


def _ubicaciones_celdas(paneles):
    ubicaciones = []
    for panel in paneles:
        entradas = [elemento for elemento in panel.contenedor.descendants() if isinstance(elemento, ui.input)]
        ubicaciones.extend({"panel": panel.contenedor.html_id, "indice": entrada._props["data-geometria-indice"]}
                           for entrada in entradas)
    return ubicaciones
