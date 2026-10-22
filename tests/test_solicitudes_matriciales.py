"""Aislamiento entre solicitudes de calculo y limpieza de las vistas matriciales."""
import asyncio

import pytest
from nicegui import run, ui

from tests.comun_construccion_vistas import construir_pagina


def cargar_captura(vista, herramienta: str) -> None:
    """Carga un caso minimo exacto en el panel correspondiente."""
    if herramienta == 'sistemas':
        vista.cuadricula.cargar_datos([['2']], ['1'])
    else:
        vista.panel_matriz_cuadrada.cargar_matriz([['2']])


def editar_captura(vista, herramienta: str) -> None:
    """Edita la celda mediante su entrada real durante una solicitud pendiente."""
    if herramienta == 'sistemas':
        vista.cuadricula.entradas_coeficientes[0][0].set_value('3')
    else:
        vista.panel_matriz_cuadrada.celdas[0][0].set_value('3')


async def calcular_captura(vista, herramienta: str, boton) -> None:
    """Invoca el manejador publico de calculo con el mismo boton entre solicitudes."""
    if herramienta == 'sistemas':
        await vista.resolver_sistema(boton)
    else:
        await vista.calcular(boton)


def bloquear_primera_solicitud(monkeypatch, falla: bool):
    """Instala un trabajador que demora solo la primera solicitud real."""
    inicio, liberar = asyncio.Event(), asyncio.Event()
    llamadas = 0
    async def trabajador(funcion, *argumentos):
        """Conserva el calculo matematico mientras controla el orden de finalizacion."""
        nonlocal llamadas
        llamadas += 1
        if llamadas == 1:
            inicio.set()
            await liberar.wait()
            if falla:
                raise RuntimeError('fallo antiguo')
        return funcion(*argumentos)
    monkeypatch.setattr(run, 'io_bound', trabajador)
    return inicio, liberar


@pytest.mark.parametrize('herramienta', ['sistemas', 'inversa'])
@pytest.mark.parametrize('falla_antigua', [False, True])
def test_solicitud_antigua_no_borra_resultado_actual(monkeypatch, herramienta, falla_antigua):
    """Una respuesta o error antiguos no modifican resultado, historial ni carga nuevos."""
    async def comprobar(vista, cliente):
        """Publica la segunda respuesta antes de liberar la primera solicitud."""
        cargar_captura(vista, herramienta)
        inicio, liberar = bloquear_primera_solicitud(monkeypatch, falla_antigua)
        boton = ui.button('Calcular')
        antigua = asyncio.create_task(calcular_captura(vista, herramienta, boton))
        await inicio.wait()
        editar_captura(vista, herramienta)
        await calcular_captura(vista, herramienta, boton)
        resultado = vista.ultimo_resultado
        textos = [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        historial = list(vista.historial)
        liberar.set()
        await antigua
        assert vista.ultimo_resultado is resultado and resultado is not None
        assert textos == [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert vista.historial == historial and len(historial) == 1
        assert boton._props['loading'] == 'false'
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize('herramienta', ['sistemas', 'inversa'])
def test_limpiar_durante_solicitud_conserva_estado_inicial(monkeypatch, herramienta):
    """La finalizacion de una solicitud cancelada por limpieza no repinta la vista."""
    async def comprobar(vista, cliente):
        """Limpia mientras espera el trabajador y comprueba el estado despues."""
        cargar_captura(vista, herramienta)
        inicio, liberar = bloquear_primera_solicitud(monkeypatch, False)
        antigua = asyncio.create_task(calcular_captura(vista, herramienta, ui.button('Calcular')))
        await inicio.wait()
        vista.limpiar_todo()
        liberar.set()
        await antigua
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert not vista.historial
        textos = [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert any('Listo para' in texto for texto in textos)
        assert not any('Los datos cambiaron' in texto for texto in textos)
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
