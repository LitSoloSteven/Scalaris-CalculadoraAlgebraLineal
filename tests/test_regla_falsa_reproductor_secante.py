"""Seguimiento del paso, fila, fórmula, secante y foco con el reproductor compartido."""
from nicegui import ui

from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion
from src.frontend.vistas.regla_falsa.procedimiento import PanelProcedimiento
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_reproductor_conserva_nodo_y_sincroniza_la_fila(monkeypatch):
    """El paso activo decide la tabla, el gráfico y la captura pedagógica sin resolver otra raíz."""
    async def comprobar(vista):
        """Recorre iteraciones reales con un solo nodo gráfico y llega al cierre del motor."""
        vista.contenedor_detalle = ui.column()
        panel = PanelProcedimiento(vista, calcular_presentacion(captura_regla_falsa()))
        panel.construir()
        grafica = panel.grafica
        assert panel.reproductor.sin_movimiento and panel.fila_activa is None
        for indice in (1, 4, len(panel.reproductor.pasos) - 1):
            panel.reproductor.ir_a(indice)
            fila = panel.reproductor.pasos[indice].cuerpo
            assert panel.grafica is grafica and panel.fila_activa is fila
            assert panel.tabla.tabla.selected[0]["i"] == str(fila["i"])
            assert vista._foco_procedimiento.captura.detalle["iteracion"] is fila
            assert panel.grafica.figure["data"][2]["x"] == [fila["aproximacion"]]
        panel.reproductor.detener()
    ejecutar_escenario(monkeypatch, comprobar)
