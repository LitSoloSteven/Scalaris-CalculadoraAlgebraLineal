"""Integración del detalle con foco, invalidación y resultados extremos reales."""
from types import SimpleNamespace

import pytest

from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_desmarcar_fila_vuelve_al_planteamiento_sin_secante(monkeypatch):
    """El evento real de deselección retira la fila de tabla, gráfico, fórmula y foco al mismo tiempo."""
    async def comprobar(vista):
        """Ejecuta el manejador de selección de NiceGUI con una deselección del usuario."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        panel = vista.detalle_procedimiento
        panel.reproductor.ir_a(4)
        tabla = panel.tabla.tabla
        fila = tabla.selected[0]
        evento = next(evento for evento in tabla._event_listeners.values() if evento.type == "selection")
        evento.handler(SimpleNamespace(args={"added": False, "rows": [fila], "keys": [fila["i"]]}))
        assert not tabla.selected and panel.tabla.fila_activa is None
        assert panel.reproductor.indice_actual == 0 and panel.fila_activa is None
        assert vista.obtener_contexto_ia().foco.captura.detalle["iteracion"] is None
        assert not any("Secante por" in traza.get("name", "") for traza in panel.grafica.figure["data"])
    ejecutar_escenario(monkeypatch, comprobar)


def test_seleccion_sincroniza_formula_grafico_y_contexto(monkeypatch):
    """El resultado conserva su identidad mientras la selección cambia el foco y la secante."""
    async def comprobar(vista):
        """Selecciona una fila y verifica los datos compartidos, ignorando valores del evento cliente."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        resultado = vista.ultimo_resultado
        panel = vista.detalle_procedimiento
        grafica = panel.grafica
        panel.tabla._elegir(SimpleNamespace(selection=[{"i": "4", "aproximacion": 999}]))
        fila = resultado["iteraciones"][3]
        assert panel.reproductor.indice_actual == 4 and panel.fila_activa is fila
        assert panel.grafica is grafica and panel.grafica.figure["data"][2]["x"] == [fila["aproximacion"]]
        foco = vista.obtener_contexto_ia().foco
        assert foco.indice == 5 and foco.captura.detalle["iteracion"] is fila
        assert panel.tabla.tabla.selected[0]["i"] == "4"
        vista.formato.set_value(12)
        assert vista.ultimo_resultado is resultado and panel.reproductor.indice_actual == 4
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("accion", ["editar", "limpiar", "cerrar"])
def test_invalidacion_detiene_reproduccion_y_retira_foco(monkeypatch, accion):
    """El reproductor anterior no deja temporizadores ni referencias visibles después de invalidar."""
    async def comprobar(vista):
        """Activa la reproducción y retira el ejercicio por distintas vías públicas."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        reproductor = vista.reproductor_pasos
        reproductor.ir_a(2)
        reproductor._alternar_reproduccion()
        assert reproductor.temporizador.active
        if accion == "editar":
            vista.expresion.set_value("x^2-3")
        elif accion == "limpiar":
            vista.limpiar_todo()
        else:
            vista.cerrar()
        assert reproductor.temporizador is None
        assert vista.detalle_procedimiento is None and vista.reproductor_pasos is None
        assert vista.obtener_contexto_ia().foco is None
        assert not list(vista.contenedor_detalle)
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambios", [{"expresion": "x", "extremo_izquierdo": "0"},
                                    {"expresion": "x+"}, {"expresion": "x^2+1"}])
def test_sin_filas_conserva_planteamiento_y_cierre_sin_secante_ficticia(monkeypatch, cambios):
    """Los resultados sin iteraciones admiten navegación sin seleccionar una fila inventada."""
    async def comprobar(vista):
        """Recorre el cierre real de una raíz de extremo, error o ausencia de cambio de signo."""
        vista.cargar_captura(captura_regla_falsa(**cambios))
        await vista.resolver()
        panel = vista.detalle_procedimiento
        assert len(panel.reproductor.pasos) == 2
        panel.reproductor.ir_a(1)
        assert panel.fila_activa is None and panel.tabla.tabla.rows == []
        assert not any("Secante por" in traza.get("name", "") for traza in panel.grafica.figure["data"])
        assert vista.obtener_contexto_ia().foco.tipo == "final"
    ejecutar_escenario(monkeypatch, comprobar)
