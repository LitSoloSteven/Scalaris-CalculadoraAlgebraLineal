"""Carga, errores y descarte de trabajo obsoleto en los flujos incorporados."""
import asyncio
from unittest.mock import Mock

import pytest
from nicegui import run, ui

from tests.comun_construccion_vistas import construir_pagina


def _boton(cliente, texto):
    return next(elemento for elemento in cliente.elements.values()
                if isinstance(elemento, ui.button) and elemento.text == texto)


def _preparar_calculo(vista, cliente, herramienta):
    if herramienta == "vectores":
        vista.pestanas.set_value("independencia")
        vista.panel_independencia.cargar_datos({"u": ["1", "2"], "v": ["2", "4"]})
        return vista.calcular(), vista.boton_calcular
    vista.cuadricula.cargar_datos([["1", "2"], ["2", "4"]], ["0", "0"])
    vista.casilla_homogeneo.set_value(True)
    boton = _boton(cliente, "Resolver")
    return vista.resolver_sistema(boton), boton


def _editar_captura(vista, herramienta):
    if herramienta == "vectores":
        vista.panel_independencia.cargar_datos({"u": ["3", "4"], "v": ["1", "0"]})
    else:
        vista.casilla_homogeneo.set_value(False)


@pytest.mark.parametrize("herramienta", ["sistemas", "vectores"])
@pytest.mark.parametrize("desmontar", [False, True])
def test_trabajo_obsoleto_no_publica_resultado_ni_reproductor(monkeypatch, herramienta, desmontar):
    """Una captura modificada o un cliente destruido descarta la respuesta real del backend."""
    async def comprobar(vista, cliente):
        """Retiene la ejecucion, modifica la pagina y libera el calculo original."""
        preparado, terminar = asyncio.Event(), asyncio.Event()
        async def trabajador(funcion, *argumentos):
            """Espera la autorizacion de la prueba y ejecuta el algoritmo real."""
            preparado.set()
            await terminar.wait()
            return funcion(*argumentos)
        monkeypatch.setattr(run, "io_bound", trabajador)
        calculo, boton = _preparar_calculo(vista, cliente, herramienta)
        tarea = asyncio.create_task(calculo)
        await preparado.wait()
        assert "loading" in boton._props
        if desmontar:
            cliente.delete()
            monkeypatch.setattr(cliente, "delete", Mock())
        else:
            _editar_captura(vista, herramienta)
        terminar.set()
        await tarea
        assert getattr(vista, "ultimo_resultado", None) is None
        assert getattr(vista, "resultado_actual", None) is None
        assert vista.reproductor_pasos is None
        if not desmontar:
            assert boton._props.get("loading") in (None, False, "false")
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize("herramienta", ["sistemas", "vectores"])
def test_fallo_trabajador_restaura_estado_y_retira_exito_anterior(monkeypatch, herramienta):
    """Un error inesperado deja mensaje y permite reintentar sin conservar un exito falso."""
    async def comprobar(vista, cliente):
        """Calcula primero, luego provoca el fallo del trabajador y examina la salida."""
        calculo, boton = _preparar_calculo(vista, cliente, herramienta)
        await calculo
        assert vista.reproductor_pasos is not None
        async def fallar(*argumentos):
            """Reproduce un fallo del trabajador sin incluir datos de captura en el mensaje."""
            raise RuntimeError("detalle privado ficticio")
        monkeypatch.setattr(run, "io_bound", fallar)
        if herramienta == "vectores":
            await vista.calcular()
        else:
            await vista.resolver_sistema(boton)
        resultado = getattr(vista, "ultimo_resultado", None) or getattr(vista, "resultado_actual", None)
        assert not resultado or resultado.get("estado") == "ERROR"
        assert vista.reproductor_pasos is None
        assert boton._props.get("loading") in (None, False, "false")
        assert vista.obtener_contexto_ia().resultado is None or vista.obtener_contexto_ia().resultado["estado"] == "ERROR"
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
