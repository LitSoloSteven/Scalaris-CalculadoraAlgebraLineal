"""Pruebas de cambio de modo, borradores independientes y paridad en Espacios y subespacios."""
import asyncio

import pytest
from nicegui import run, ui

from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


@pytest.fixture(autouse=True)
def registrar_vista_subespacios(monkeypatch):
    """Habilita el constructor real de Espacios y subespacios en las rutas de prueba."""
    monkeypatch.setitem(VISTAS_RUTAS, "espacios_subespacios", (
        "algebra.operaciones_vectores.vista_espacios_subespacios", "VistaEspaciosSubespacios",
    ))


def _pulsar_boton(boton: ui.button) -> None:
    for escucha in boton._event_listeners.values():
        if escucha.type == "click":
            escucha.handler(None)


@pytest.mark.parametrize(("parametros", "modo_esperado", "etiqueta"), [
    ({}, "generadores", "Generadores"),
    ({"modo": "generadores"}, "generadores", "Generadores"),
    ({"modo": "restricciones"}, "restricciones", "Restricciones"),
    ({"modo": "desconocido"}, "generadores", "Generadores"),
])
def test_ruta_inicial_selecciona_modo_subespacios(monkeypatch, parametros, modo_esperado, etiqueta):
    """La URL base y valores desconocidos abren Generadores; ?modo=restricciones abre Restricciones."""
    async def comprobar(vista, _cliente):
        """Comprueba el modo activo, las pestañas y el contexto inicial."""
        assert vista.modo == modo_esperado
        assert vista.selector_modo.value == modo_esperado
        assert vista.obtener_contexto_ia().etiqueta == etiqueta

    asyncio.run(construir_pagina(monkeypatch, "espacios_subespacios", comprobar, parametros))


def test_cambio_modo_conserva_borradores_y_navega_contraejemplos(monkeypatch):
    """Alternar modos conserva borradores, limpia resultado y enlaza los tres contraejemplos."""
    async def comprobar(vista, _cliente):
        """Edita ambos modos, analiza el ejemplo afín y navega sus criterios."""
        vista.captura_generadores.cargar_generadores({"v_1": ["2", "0", "0"]})
        await vista.analizar()
        assert vista.ultimo_resultado["dimension"] == 1

        vista.selector_modo.set_value("restricciones")
        assert vista.modo == "restricciones"
        assert vista.ultimo_resultado is None
        assert vista.captura_generadores.obtener()["vectores"]["v_1"]["datos"] == ["2", "0", "0"]

        vista.captura.cargar_ejemplo()
        await vista.analizar()
        assert vista.ultimo_resultado["clasificacion"] == "AFIN_NO_SUBESPACIO"
        botones = [
            elemento for elemento in vista.contenedor_resultados.descendants()
            if isinstance(elemento, ui.button) and "subespacios-criterio-boton" in elemento.classes
        ]
        assert len(botones) == 3
        claves = []
        for boton in botones:
            _pulsar_boton(boton)
            paso = vista.reproductor_pasos.pasos[vista.reproductor_pasos.indice_actual]
            claves.append(paso.cuerpo[1]["clave"])
        assert claves == ["origen", "suma", "escalar"]

        vista.selector_modo.set_value("generadores")
        assert vista.ultimo_resultado is None
        assert vista.captura.obtener()["vectores"]["v_1"]["datos"] == ["2", "0", "0"]
        vista.selector_modo.set_value("restricciones")
        assert vista.captura.obtener()["matriz_a"] == [["-1", "-1", "1"]]

    asyncio.run(construir_pagina(monkeypatch, "espacios_subespacios", comprobar))


def test_paridad_matriz_ecuaciones_ceros_y_conversion_invalida(monkeypatch):
    """y=0 en ℝ², 0x1=0 con ceros explícitos y conversión fallida conservan la captura."""
    async def comprobar(vista, _cliente):
        """Comprueba ida y vuelta exacta entre Ecuaciones y Matriz."""
        captura = vista.captura
        captura.establecer_dimension_ambiente(2)
        captura.selector.set_value("ecuaciones")
        captura.ecuaciones.set_value("y = 0")
        captura.selector.set_value("matriz")
        assert captura.obtener()["matriz_a"] == [["0", "1"]]
        await vista.analizar()
        assert vista.ultimo_resultado["dimension"] == 1
        assert vista.ultimo_resultado["base"] == (("1", "0"),)

        captura.selector.set_value("ecuaciones")
        captura.ecuaciones.set_value("0x1 = 0")
        captura.selector.set_value("matriz")
        assert captura.obtener()["matriz_vacia"] is False
        await vista.analizar()
        assert vista.ultimo_resultado["dimension"] == 2

        captura.selector.set_value("ecuaciones")
        captura.ecuaciones.set_value("z = 0")
        captura.selector.set_value("matriz")
        assert captura.formato == "ecuaciones"
        assert captura.ecuaciones.value == "z = 0"
        assert captura.ecuaciones._props.get("aria-invalid") == "true"

    asyncio.run(construir_pagina(monkeypatch, "espacios_subespacios", comprobar, {"modo": "restricciones"}))


@pytest.mark.parametrize("falla", [False, True])
def test_cambio_modo_detiene_reproduccion_y_descarta_en_vuelo(monkeypatch, falla):
    """Cambiar de modo detiene el reproductor e impide respuestas o fallos tardíos del modo previo."""
    async def comprobar(vista, _cliente):
        """Detiene un temporizador activo y retiene una solicitud de restricciones durante el cambio."""
        vista.captura.cargar_ejemplo()
        await vista.analizar()
        vista.reproductor_pasos._alternar_reproduccion()
        temporizador = vista.reproductor_pasos.temporizador
        assert temporizador.active
        vista.selector_modo.set_value("generadores")
        assert temporizador.is_deleted
        assert vista.reproductor_pasos is None

        vista.selector_modo.set_value("restricciones")
        iniciado, liberar = asyncio.Event(), asyncio.Event()

        async def ejecutar(calcular, captura):
            """Retiene el cálculo de restricciones hasta que generadores publique su resultado."""
            if captura["modo"] == "restricciones":
                iniciado.set()
                await liberar.wait()
                if falla:
                    raise RuntimeError("fallo tardio")
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", ejecutar)
        tarea_antigua = asyncio.create_task(vista.analizar())
        await iniciado.wait()
        vista.selector_modo.set_value("generadores")
        assert vista.boton_analizar.props.get("loading") == "false"
        vista.captura.cargar_ejemplo()
        await vista.analizar()
        vigente = vista.ultimo_resultado
        liberar.set()
        await tarea_antigua
        assert vista.ultimo_resultado is vigente
        assert vigente["modo"] == "generadores"
        assert vista.estado.text == ""

    asyncio.run(construir_pagina(monkeypatch, "espacios_subespacios", comprobar, {"modo": "restricciones"}))
