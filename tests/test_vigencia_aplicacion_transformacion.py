"""Vigencia y estados asíncronos del recorrido de aplicación de matrices."""
import asyncio
import json
from unittest.mock import Mock

import pytest
from nicegui import run, ui

from src.frontend import textos_transformaciones as textos
from src.frontend.controladores.operaciones_matrices.controlador_aplicacion_transformacion import (
    ControladorAplicacionTransformacion,
)
from src.frontend.vistas.operaciones_matrices._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from tests.comun_construccion_vistas import construir_pagina


def _alterar_captura(vista, cambio):
    if cambio == "vector":
        vista.entradas_vector_original[0].set_value("7")
        vista.entradas_vector_original[0].set_value("3")
    elif cambio == "modo":
        vista.selector_modo.set_value(textos.MODO_ANALISIS)
        vista.selector_modo.set_value(textos.MODO_APLICACION)
    elif cambio == "tipo":
        vista.selector_tipo_objeto.set_value("punto")
        vista.selector_tipo_objeto.set_value("vector")
    elif cambio == "dimension":
        vista._aplicar_dimension("columnas", 3)
        vista._aplicar_dimension("columnas", 2)
    elif cambio == "limpieza":
        vista.limpiar_todo()
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
    else:
        vista.contenedor_resultados.delete()


@pytest.mark.parametrize("cambio", ["vector", "modo", "tipo", "dimension", "limpieza", "desmontaje"])
def test_respuesta_tardia_no_se_publica_incluso_si_se_restaura_captura(monkeypatch, cambio):
    """No publica respuestas de una revisión anterior aunque el texto vuelva al original."""
    async def comprobar(vista, cliente):
        """Retiene el trabajador mientras cambia la captura o desaparece el panel."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        iniciado, continuar = asyncio.Event(), asyncio.Event()

        async def trabajador(funcion, *argumentos):
            """Espera permiso del escenario y luego calcula con la captura original."""
            iniciado.set()
            await continuar.wait()
            return funcion(*argumentos)

        monkeypatch.setattr(run, "io_bound", trabajador)
        tarea = asyncio.create_task(vista._analizar(vista.boton_calcular))
        await iniciado.wait()
        _alterar_captura(vista, cambio)
        continuar.set()
        await tarea
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert not vista.boton_calcular._props.get("loading", False)
        assert not vista._calculando
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_carga_visible_impide_aplicaciones_simultaneas(monkeypatch):
    """Muestra carga antes del trabajador y evita dos cálculos simultáneos."""
    async def comprobar(vista, cliente):
        """Inspecciona el estado intermedio de una aplicación y su resultado final."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        iniciado, continuar = asyncio.Event(), asyncio.Event()
        llamadas = Mock()

        async def trabajador(funcion, *argumentos):
            """Registra la delegación y espera para mantener visible la carga."""
            llamadas()
            iniciado.set()
            await continuar.wait()
            return funcion(*argumentos)

        monkeypatch.setattr(run, "io_bound", trabajador)
        tarea = asyncio.create_task(vista._analizar(vista.boton_calcular))
        await iniciado.wait()
        assert vista.boton_calcular._props["loading"] is True
        assert any(isinstance(elemento, ui.label) and elemento.text == "Calculando…"
                   for elemento in vista.contenedor_resultados.descendants())
        await vista._analizar(vista.boton_calcular)
        llamadas.assert_called_once()
        continuar.set()
        await tarea
        assert vista.ultimo_resultado["vector_transformado"]["exacta"] == ["3", "2"]
        assert not vista.boton_calcular._props.get("loading", False)
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_comprobacion_fallida_no_se_presenta_como_exito(monkeypatch):
    """Una discrepancia produce aviso accesible sin mostrar coordenadas certificadas."""
    async def comprobar(vista, cliente):
        """Simula solo la respuesta discrepante para comprobar la decisión de presentación."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        respuesta = json.dumps({"estado": "EXITO", "verificacion": False})
        monkeypatch.setattr(ControladorAplicacionTransformacion, "procesar", lambda carga: respuesta)
        await vista._analizar(vista.boton_calcular)
        etiquetas = [elemento for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert len(etiquetas) == 1 and etiquetas[0].text == textos.ERROR_COMPROBACION
        assert etiquetas[0]._props["role"] == "alert"
        assert vista.reproductor_pasos is None
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
