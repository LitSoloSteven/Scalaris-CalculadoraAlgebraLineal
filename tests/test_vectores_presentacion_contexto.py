"""Cálculo completo, vigencia de contexto y escape de la presentación vectorial."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend.vistas.operaciones_vectores.vista_operaciones_vectores import VistaOperacionesVectores
from tests.comun_clientes import PanelIASimulado
from tests.comun_vista_vectorial import vista_vectorial_montada, ejecutar_calculo_en_panel


@pytest.mark.parametrize("operacion", ["suma_resta", "escalar", "combinacion_lineal"])
def test_calculo_completo_monta_resultado_y_contexto_vigente(vista_vectorial_montada, operacion):
    """La captura real llega al controlador, al reproductor y al contexto sin fallos."""
    vista = vista_vectorial_montada
    vista.pestanas.set_value(operacion)
    for vector in vista.panel_vectorial.vectores.values():
        vector["celdas"] = {0: "1/3", 1: "2", 2: "-3"}
    asyncio.run(ejecutar_calculo_en_panel(vista))
    assert vista.resultado_actual["estado"] != "ERROR"
    assert vista.reproductor_pasos is not None
    assert vista.boton_calcular.enabled
    assert "loading" not in vista.boton_calcular._props
    contexto = vista.obtener_contexto_ia()
    assert contexto.desactualizado is False
    assert contexto.resultado["estado"] == vista.resultado_actual["estado"]
    siguiente = next(iter(vista.panel_vectorial.vectores.values()))
    siguiente["celdas"][0] = "9"
    contexto = vista.obtener_contexto_ia()
    assert contexto.desactualizado is True
    assert contexto.resultado is None


def test_contexto_detecta_orientacion_modificada(vista_vectorial_montada):
    """La orientación también participa en la identidad del ejercicio calculado."""
    vista = vista_vectorial_montada
    asyncio.run(ejecutar_calculo_en_panel(vista))
    vista.panel_suma_resta.alternar_orientacion("u")
    contexto = vista.obtener_contexto_ia()
    assert contexto.desactualizado is True
    assert contexto.resultado is None
    assert contexto.entrada["u"]["orientacion"] == "fila"


def test_presentacion_escapa_latex_y_coeficientes(vista_vectorial_montada):
    """El texto recibido nunca se interpreta como etiquetas HTML en el resumen."""
    vista = vista_vectorial_montada
    with vista.panel_resultados:
        vista.renderizar_resultado_basico({"vector_resultado_latex": "<img src=x onerror=alert(1)>"})
        vista.renderizar_resultado_combinacion({"estado": "UNICA", "coeficientes_texto": ["<script>x</script>"]})
    contenidos = [elemento.content for elemento in vista.panel_resultados.descendants() if isinstance(elemento, ui.html)]
    assert any("&lt;img" in contenido for contenido in contenidos)
    assert any("&lt;script&gt;" in contenido for contenido in contenidos)
    assert all("<script>" not in contenido and "<img " not in contenido for contenido in contenidos)


@pytest.mark.parametrize('panel_lateral', [False, True])
def test_construccion_completa_monta_asistente_y_tres_paneles(monkeypatch, panel_lateral):
    """El montaje usa componentes reales con almacén aislado para las dos modalidades."""
    from src.frontend.vistas.operaciones_vectores import vista_operaciones_vectores as modulo
    monkeypatch.setattr(modulo, "PanelIA", PanelIASimulado)
    monkeypatch.setattr(ui, "run_javascript", Mock())
    from src.frontend import banderas
    monkeypatch.setattr(banderas, "panel_lateral_habilitado", lambda: panel_lateral)
    monkeypatch.setattr(banderas, "navegacion_actualizada", lambda: False)
    vista = VistaOperacionesVectores()
    cliente = ui.context.client
    monkeypatch.setattr(cliente, "run_javascript", Mock())
    anteriores = set(cliente.elements)
    try:
        vista.construir()
        assert vista.panel_ia.interfaz_activa is vista
        assert [len(panel.vectores) for panel in vista.paneles.values()] == [2, 1, 2]
        assert vista.panel_resultados is not None
        assert vista.boton_calcular is not None
        if not panel_lateral:
            boton = next(elemento for elemento in cliente.elements.values()
                         if isinstance(elemento, ui.button) and elemento._props.get("aria-label") == "Glosa")
            manejador = next(iter(boton._event_listeners.values())).handler
            manejador(SimpleNamespace(sender=boton))
            assert vista.panel_ia.esta_abierto is True
    finally:
        for elemento in list(cliente.elements.values()):
            if elemento.id not in anteriores and not elemento.is_deleted:
                elemento.delete()
