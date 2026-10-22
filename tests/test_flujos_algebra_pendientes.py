"""Integracion real de capturas, controladores, resultados, reproductor y Glosa."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina


def _boton(cliente, texto):
    return next(elemento for elemento in cliente.elements.values()
                if isinstance(elemento, ui.button) and elemento.text == texto)


def _recorrer_reproductor(vista):
    reproductor = vista.reproductor_pasos
    assert reproductor is not None
    for indice in range(len(reproductor.pasos)):
        reproductor.ir_a(indice)
    assert any(paso.tipo == "verificacion" for paso in reproductor.pasos)


@pytest.mark.parametrize("metodo", ["gauss", "gauss-jordan"])
@pytest.mark.parametrize("datos,solo_trivial", [
    ([["1", "0"], ["0", "1"]], True),
    ([["1", "2"], ["2", "4"]], False),
])
def test_modo_homogeneo_fija_b_y_presenta_familia_verificada(monkeypatch, metodo, datos, solo_trivial):
    """El flujo actual de sistemas resuelve Ax=0 sin capturar b ni repetir el algoritmo."""
    async def comprobar(vista, cliente):
        """Resuelve desde controles visibles y restaura los terminos generales al salir."""
        vista.cuadricula.cargar_datos(datos, ["3", "4"])
        vista.pestanas_metodo.set_value(metodo)
        vista.casilla_homogeneo.set_value(True)
        assert vista.cuadricula.obtener_datos_matriz()[1] == ["0", "0"]
        assert all(celda._props["readonly"] for celda in vista.cuadricula.entradas_independientes)
        await vista.resolver_sistema(_boton(cliente, "Resolver"))
        resultado = vista.ultimo_resultado["homogeneo"]
        assert resultado["solo_trivial"] is solo_trivial
        assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])
        _recorrer_reproductor(vista)
        assert vista.obtener_contexto_ia().resultado["solo_trivial"] is solo_trivial
        assert any(isinstance(elemento, ui.button) and elemento.text == "Ver en el Visualizador"
                   for elemento in cliente.elements.values())
        vista.casilla_homogeneo.set_value(False)
        assert vista.cuadricula.obtener_datos_matriz()[1] == ["3", "4"]
        assert vista.ultimo_resultado is None
        assert vista.reproductor_pasos is None
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))


def test_importar_ecuaciones_generales_desactiva_homogeneo_sin_perder_b(monkeypatch):
    """Volver desde ecuaciones con b no nulo conserva su sistema y sincroniza la casilla."""
    async def comprobar(vista, cliente):
        """Reproduce la importacion despues de haber resuelto una captura homogenea."""
        vista.cuadricula.cargar_datos([["1"]], ["3"])
        vista.casilla_homogeneo.set_value(True)
        vista.pestanas_modo.set_value("Ecuaciones")
        vista.entradas_ecuaciones[0].set_value("x1=7")
        vista.pestanas_modo.set_value("Matriz")
        assert vista.casilla_homogeneo.value is False
        assert vista.cuadricula.modo_homogeneo is False
        assert vista.cuadricula.obtener_datos_matriz() == ([["1"]], ["7"])
        await vista.resolver_sistema(_boton(cliente, "Resolver"))
        assert vista.ultimo_resultado["solucion"] == ["7"]
        assert "homogeneo" not in vista.ultimo_resultado
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))


@pytest.mark.parametrize("datos,independiente", [
    ({"u": ["1", "0"], "v": ["0", "1"]}, True),
    ({"u": ["1/2", "1/3"], "v": ["1", "2/3"]}, False),
])
def test_independencia_desde_pestana_vectorial_y_transferencia(monkeypatch, datos, independiente):
    """La pestana permite calcular LI/LD con relaciones verificadas, Glosa y visualizador."""
    async def comprobar(vista, cliente):
        """Recorre el calculo y sus pasos, sin introducir rutas ni resultados simulados."""
        vista.pestanas.set_value("independencia")
        vista.panel_independencia.cargar_datos(datos)
        await vista.calcular()
        resultado = vista.resultado_actual
        assert resultado["estado"] == "EXITO"
        assert resultado["es_independiente"] is independiente
        assert bool(resultado["relaciones"]) is (not independiente)
        assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])
        _recorrer_reproductor(vista)
        assert vista.obtener_contexto_ia().resultado["es_independiente"] is independiente
        assert any(isinstance(elemento, ui.button) and elemento.text == "Ver en el Visualizador"
                   for elemento in cliente.elements.values())
        vista.pestanas.set_value("suma_resta")
        assert vista.resultado_actual is None
        assert vista.reproductor_pasos is None
    asyncio.run(construir_pagina(monkeypatch, "vectores", comprobar))
