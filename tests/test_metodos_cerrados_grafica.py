"""Identidad de Plotly, trazas vigentes e inclusión de recursos de la vista interna."""
import asyncio
from types import SimpleNamespace

from nicegui.elements.plotly import Plotly

from src.frontend.presentacion.recursos_vistas import seleccionar_recursos
from src.frontend.tema import _CABECERA_HTML
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from tests.test_metodos_cerrados_calculo import montar_vista


def test_grafica_unica_sincronizada_y_previa_independiente(monkeypatch):
    """Sigue los cambios de captura, fila, paso, método y limpieza en un mismo nodo."""
    async def comprobar():
        """Inspecciona el nodo original antes y después de cada transición."""
        async with montar_vista(monkeypatch) as (vista, cliente):
            nodo = vista.grafica.nodo
            vista.cargar_captura({"expresion": "x^2 - 2", "extremo_izquierdo": "1"})
            await vista.grafica.tarea
            assert len(nodo.figure.data[0].x) > 10
            assert list(nodo.figure.data[-1].x) == [1.0]
            vista.captura.superior.set_value("2")
            for metodo, etiqueta in ((BISECCION, "Punto medio c"), (REGLA_FALSA, "Cruce de secante (c, 0)")):
                revision = nodo.figure.layout.uirevision
                vista.captura.metodo.set_value(metodo)
                assert nodo.figure.layout.uirevision == revision
                await vista.resolver()
                tabla = vista.salida.tabla
                tabla._elegir(SimpleNamespace(selection=[tabla.tabla.rows[0]]))
                assert vista.salida.reproductor.indice_actual == 1
                assert etiqueta in [traza.name for traza in nodo.figure.data]
                vista.salida.reproductor.ir_a(2)
                assert tabla.fila_activa == "2"
                assert vista.salida.fila is vista.ultimo_resultado["iteraciones"][1]
                assert [elemento for elemento in cliente.elements.values() if isinstance(elemento, Plotly)] == [nodo]
            vista.limpiar_todo()
            assert vista.ultimo_resultado is None
            assert [traza.name for traza in nodo.figure.data] == ["f(x)"]
            assert vista.grafica.nodo is nodo
    asyncio.run(comprobar())


def test_hoja_compartida_llega_solo_a_sus_consumidores():
    """Mantiene aislados abiertos, cerrados y las rutas anteriores."""
    for vista in ("inicio", "biseccion", "regla_falsa", "metodos_abiertos", "metodos_cerrados"):
        html = seleccionar_recursos(_CABECERA_HTML, vista)
        assert ("estructura_metodos_raices.css" in html) == vista.startswith("metodos_")
        assert ("vistas_metodos_cerrados.css" in html) == (vista == "metodos_cerrados")


def test_intervalo_en_grados_amplia_rango_por_defecto_y_permite_ajustarlo(monkeypatch):
    """El resultado queda a la vista y el ajuste manual conserva ejercicio y cálculo."""
    async def comprobar():
        """Encuadra una solución en grados después de preparar la curva inicial."""
        async with montar_vista(monkeypatch, REGLA_FALSA) as (vista, _):
            vista.captura.ejemplos.set_value("Seno en grados")
            await vista.grafica.tarea
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (-10, 10)
            await vista.resolver()
            figura = vista.grafica.nodo.figure
            assert tuple(figura.layout.xaxis.range) == (0, 60)
            assert max(figura.data[0].x) == 60
            resultado, captura = vista.ultimo_resultado, vista.capturar()
            vista.captura.definir_rango((-5, 5))
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (-5, 5)
            vista.grafica.ajustar_intervalo()
            await vista.grafica.tarea
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (0, 60)
            assert vista.ultimo_resultado is resultado
            assert vista.capturar() == captura
    asyncio.run(comprobar())
