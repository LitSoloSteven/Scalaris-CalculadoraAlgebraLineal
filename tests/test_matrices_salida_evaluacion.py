"""Salida de Matrices durante la evaluacion y limpieza de su reproductor."""
import asyncio
from unittest.mock import Mock

import pytest
from nicegui import run, ui

from src.frontend.textos import LIMPIAR
from tests.comun_construccion_vistas import construir_pagina


def _preparar_expresion(vista, cliente):
    vista.panel_captura_matrices.cargar_datos({"A": [["1/3"]]})
    vista.entrada_expresion.set_value("A+A")
    return next(elemento for elemento in cliente.elements.values()
                if isinstance(elemento, ui.button) and elemento.text == "Evaluar")


def test_panel_expresion_solo_ofrece_limpieza_y_evaluacion(monkeypatch):
    """La captura conserva Evaluar sin el selector ni el boton de factorizacion."""
    async def comprobar(vista, cliente):
        """Inspecciona controles reales y evalua una expresion con contexto vigente."""
        boton = _preparar_expresion(vista, cliente)
        panel = vista.entrada_expresion.parent_slot.parent
        botones = [elemento for elemento in panel.descendants() if isinstance(elemento, ui.button)]
        assert len(botones) == 2
        assert botones[0]._props["aria-label"] == LIMPIAR
        assert botones[1] is boton
        assert not any(isinstance(elemento, ui.select) for elemento in panel.descendants())
        await vista.evaluar_expresion(boton)
        assert vista.ultimo_resultado["matriz_resultado"]["datos"] == [["2/3"]]
        assert vista.obtener_contexto_ia().resultado["variable_final"]
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_salida_durante_espera_inicial_no_toca_elementos_borrados(monkeypatch):
    """Salir antes del trabajador evita incluso restablecer el contenedor eliminado."""
    async def comprobar(vista, cliente):
        """Borra el cliente en el primer cambio de tarea y vigila el contenedor."""
        boton = _preparar_expresion(vista, cliente)
        trabajador = Mock()
        monkeypatch.setattr(run, "io_bound", trabajador)
        tarea = asyncio.create_task(vista.evaluar_expresion(boton))
        await asyncio.sleep(0)
        version = vista._version_solicitud
        cliente.delete()
        monkeypatch.setattr(cliente, "delete", Mock())
        restablecer = Mock(side_effect=AssertionError("Contenedor eliminado"))
        monkeypatch.setattr(vista, "restablecer_resultados", restablecer)
        await tarea
        trabajador.assert_not_called()
        restablecer.assert_not_called()
        assert vista._version_solicitud > version
        assert not vista._calculando
        assert vista.ultimo_resultado is None
        assert vista.reproductor_pasos is None
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


@pytest.mark.parametrize("salir", [False, True])
@pytest.mark.parametrize("fallar", [False, True])
def test_evaluacion_obsoleta_descarta_respuesta_y_error(monkeypatch, salir, fallar):
    """Editar o salir durante el trabajador descarta tanto resultados como excepciones."""
    async def comprobar(vista, cliente):
        """Retiene el trabajador hasta invalidar la captura o borrar el cliente."""
        boton = _preparar_expresion(vista, cliente)
        iniciado, terminar = asyncio.Event(), asyncio.Event()
        async def trabajador(funcion, *argumentos):
            """Libera el calculo real o su fallo solo despues de invalidar la vista."""
            iniciado.set()
            await terminar.wait()
            if fallar:
                raise RuntimeError("Detalle privado de prueba")
            return funcion(*argumentos)
        monkeypatch.setattr(run, "io_bound", trabajador)
        tarea = asyncio.create_task(vista.evaluar_expresion(boton))
        await iniciado.wait()
        assert boton._props["loading"] is True
        if salir:
            cliente.delete()
            monkeypatch.setattr(cliente, "delete", Mock())
        else:
            vista.entrada_expresion.set_value("A*A")
        publicar = Mock(side_effect=AssertionError("Publicacion obsoleta"))
        monkeypatch.setattr(vista.contenedor_resultados, "clear", publicar)
        terminar.set()
        await tarea
        publicar.assert_not_called()
        assert vista.ultimo_resultado is None
        assert vista.reproductor_pasos is None
        assert not vista._calculando
        if not salir:
            assert not boton._props.get("loading")
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_salida_detiene_temporizador_del_reproductor(monkeypatch):
    """Borrar el cliente retira inmediatamente el temporizador activo de los pasos."""
    async def comprobar(vista, cliente):
        """Inicia la reproduccion real y comprueba su limpieza al borrar el cliente."""
        boton = _preparar_expresion(vista, cliente)
        vista.entrada_expresion.set_value("(A+A)*A")
        await vista.evaluar_expresion(boton)
        reproductor = vista.reproductor_pasos
        reproductor._alternar_reproduccion()
        temporizador = reproductor.temporizador
        assert temporizador is not None and temporizador.active
        cliente.delete()
        monkeypatch.setattr(cliente, "delete", Mock())
        assert temporizador.is_deleted
        assert reproductor.temporizador is None
        assert vista.reproductor_pasos is None
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))
