"""Pruebas de extensión dinámica de cámara y remuestreo en los cuatro métodos de raíces."""
import asyncio
from types import SimpleNamespace

import pytest

from src.frontend.componentes.raices.captura.modos_captura_raices import MODO_BUSQUEDA
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from tests.comun_construccion_vistas import construir_pagina
from tests.test_metodos_cerrados_calculo import captura_ejercicio, montar_vista
from tests.test_metodos_cerrados_exploracion import _buscar, _resolver_lote


def _relayout_cerrados(grafica, **datos):
    grafica._encuadrar_busqueda(SimpleNamespace(args={"identidad": grafica.identidad, **datos}))


def _relayout_abiertos(previa, **datos):
    previa._encuadrar(SimpleNamespace(args={"identidad": previa.identidad, **datos}))


@pytest.mark.parametrize("metodo", (BISECCION, REGLA_FALSA))
def test_cerrados_extiende_desplaza_y_restablece_conservando_estado(monkeypatch, metodo):
    """Bisección y Regla falsa extienden f(x)=x-2 sin mutar intervalo, búsqueda ni cálculo."""
    async def _comprobar():
        async with montar_vista(monkeypatch, metodo) as (vista, _):
            vista.cargar_captura(captura_ejercicio("x - 2", "0", "4", "radianes"))
            await vista.resolver()
            resultado = vista.ultimo_resultado
            captura_inicial = vista.capturar()
            rango_busqueda = vista.exploracion.capturar_rango()

            _relayout_cerrados(vista.grafica, **{"xaxis.range[0]": -100, "xaxis.range[1]": 100})
            await vista.grafica.tarea
            curva = vista.grafica.nodo.figure.data[0]
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (-100, 100)
            assert min(curva.x) == -100 and max(curva.x) == 100

            _relayout_cerrados(vista.grafica, **{"xaxis.range": [20, 40]})
            await vista.grafica.tarea
            curva = vista.grafica.nodo.figure.data[0]
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (20, 40)
            assert min(curva.x) == 20 and max(curva.x) == 40

            _relayout_cerrados(vista.grafica, **{"xaxis.autorange": True})
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (-10, 10)
            assert vista.ultimo_resultado is resultado
            assert vista.capturar() == captura_inicial
            assert vista.exploracion.capturar_rango() == rango_busqueda

    asyncio.run(_comprobar())


@pytest.mark.parametrize("metodo", ("newton", "secante"))
def test_abiertos_extiende_desplaza_y_restablece_conservando_estado(monkeypatch, metodo):
    """Newton y Secante extienden f(x)=x-2 sin mutar semillas ni resultado previo."""
    async def _comprobar(vista, _):
        vista.metodo.set_value(metodo)
        vista.expresion.set_value("x - 2")
        vista.x0.set_value("1")
        vista.x1.set_value("3")
        await vista.previa.actualizar()
        vista.calcular()
        resultado = vista.ultimo_resultado

        _relayout_abiertos(vista.previa, **{"xaxis.range[0]": -100, "xaxis.range[1]": 100})
        await vista.previa.tarea
        curva = vista.grafica.figure.data[0]
        assert tuple(vista.grafica.figure.layout.xaxis.range) == (-100, 100)
        assert min(curva.x) == -100 and max(curva.x) == 100

        _relayout_abiertos(vista.previa, **{"xaxis.range": [20, 40]})
        await vista.previa.tarea
        curva = vista.grafica.figure.data[0]
        assert tuple(vista.grafica.figure.layout.xaxis.range) == (20, 40)
        assert min(curva.x) == 20 and max(curva.x) == 40

        _relayout_abiertos(vista.previa, **{"xaxis.autorange": True})
        await vista.previa.tarea
        assert vista.ultimo_resultado is resultado
        assert vista.x0.value == "1" and vista.x1.value == "3"
        assert vista.expresion.value == "x - 2"

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))


@pytest.mark.parametrize("metodo", ("newton", "secante"))
def test_abiertos_asintota_y_dominio_fuera_de_rango_inicial(monkeypatch, metodo):
    """1/(x-20) corta en la asíntota y sqrt(x-20) refleja su dominio al calcular o explorar."""
    async def _comprobar(vista, _):
        vista.metodo.set_value(metodo)
        vista.expresion.set_value("1/(x-20)")
        vista.x0.set_value("19")
        vista.x1.set_value("19.5")
        await vista.previa.actualizar()
        vista.calcular()
        if vista.previa.tarea is not None:
            await vista.previa.tarea
        _relayout_abiertos(vista.previa, **{"xaxis.range": [18, 22]})
        await vista.previa.tarea
        curva = vista.grafica.figure.data[0]
        assert None in curva.y

        vista.expresion.set_value("sqrt(x-20)")
        await vista.previa.actualizar()
        assert all(valor is None for valor in vista.grafica.figure.data[0].y)
        assert "No hay muestras reales" in vista.previa.estado.text

        vista.x0.set_value("21")
        vista.x1.set_value("22")
        vista.calcular()
        if vista.previa.tarea is not None:
            await vista.previa.tarea
        assert any(valor is not None for valor in vista.grafica.figure.data[0].y)

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))


@pytest.mark.parametrize("metodo", (BISECCION, REGLA_FALSA))
def test_cerrados_asintota_dominio_y_eventos_rapidos(monkeypatch, metodo):
    """Corta asíntotas en x=20, respeta dominio de sqrt(x-20) y conserva el último encuadre."""
    async def _comprobar():
        async with montar_vista(monkeypatch, metodo) as (vista, _):
            vista.cargar_captura(captura_ejercicio("1/(x-20)", "19", "21", "radianes"))
            _relayout_cerrados(vista.grafica, **{"xaxis.range": [-100, 100]})
            _relayout_cerrados(vista.grafica, **{"xaxis.range": [18, 22]})
            await vista.grafica.tarea
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (18, 22)
            assert None in vista.grafica.nodo.figure.data[0].y

            _relayout_cerrados(vista.grafica, **{"xaxis.range": [10, 10]})
            assert "no se puede representar" in vista.grafica.estado.text

            vista.cargar_captura(captura_ejercicio("sqrt(x-20)", "21", "25", "radianes"))
            await vista.grafica.tarea
            assert "No hay muestras reales" in vista.grafica.estado.text
            _relayout_cerrados(vista.grafica, **{"xaxis.range": [20, 40]})
            await vista.grafica.tarea
            assert any(valor is not None for valor in vista.grafica.nodo.figure.data[0].y)

    asyncio.run(_comprobar())


def test_cerrados_busqueda_y_detalle_no_mutan_formulario_ni_resultados(monkeypatch):
    """El zoom/pan en búsqueda y en detalle conserva rango de búsqueda y lote previos."""
    async def _comprobar():
        async with montar_vista(monkeypatch, BISECCION) as (vista, cliente):
            vista.cargar_captura(captura_ejercicio("(x+1)*(x-1)*(x-2)", "0.5", "1.5", "radianes"))
            lote = await _buscar(vista, cliente)
            await _resolver_lote(lote, BISECCION)
            rango_busqueda = vista.exploracion.capturar_rango()
            resultados_previos = vista.exploracion.respuesta
            lote_previo = lote.respuesta

            _relayout_cerrados(vista.grafica, **{"xaxis.range": [-50, 50]})
            await vista.grafica.tarea
            assert tuple(vista.grafica.nodo.figure.layout.xaxis.range) == (-50, 50)
            assert vista.exploracion.capturar_rango() == rango_busqueda
            assert vista.exploracion.respuesta is resultados_previos
            assert vista.exploracion.lote.respuesta is lote_previo

    asyncio.run(_comprobar())
