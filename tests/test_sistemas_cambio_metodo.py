"""Cambio de metodo con captura persistente y calculos anteriores invalidados."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina
from tests.test_solicitudes_matriciales import bloquear_primera_solicitud


@pytest.mark.parametrize("modo", ["Matriz", "Ecuaciones"])
def test_cambios_rapidos_conservan_captura_y_retiran_resultado(monkeypatch, modo):
    """Cambiar de ida y vuelta no recupera solucion, huella ni reproductor anteriores."""
    async def comprobar(vista, cliente):
        """Alterna metodos tras resolver y compara ambas capturas editables."""
        vista.cuadricula.cargar_datos([["2", "0"], ["0", "3"]], ["1", "7"])
        vista.pestanas_modo.set_value(modo)
        await vista.resolver_sistema(ui.button("Resolver prueba"))
        assert vista.ultimo_resultado["estado"] == "SOLUCION_UNICA"
        vista.panel_ia.establecer_foco_explicacion({
            "indice": 0, "total": 1, "tipo": "operacion", "operacion": "Paso de Gauss anterior",
        })
        captura = vista.cuadricula.obtener_datos_matriz()
        ecuaciones = [entrada.value for entrada in vista.entradas_ecuaciones]
        llamadas = []
        monkeypatch.setattr(ui, "run_javascript", llamadas.append)
        for metodo in ("gauss-jordan", "gauss", "gauss-jordan", "gauss"):
            vista.pestanas_metodo.set_value(metodo)
            assert vista.ultimo_resultado is None
            assert vista._huella_resultado is None
            assert vista.reproductor_pasos is None
            assert vista.obtener_contexto_ia().resultado is None
            assert vista.panel_ia.foco_explicacion is None
            assert "Paso de Gauss anterior" not in vista.panel_ia._recopilar_contexto()
        assert vista.pestanas_modo.value == modo
        assert vista.cuadricula.obtener_datos_matriz() == captura
        assert [entrada.value for entrada in vista.entradas_ecuaciones] == ecuaciones
        assert (vista.cuadricula.filas, vista.cuadricula.columnas) == (2, 2)
        assert llamadas.count("window.scalaris.animarCambioMetodo();") == 4
        assert any(elemento.text == "Listo para resolver" for elemento in
                   vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label))
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))


@pytest.mark.parametrize("falla_antigua", [False, True])
def test_cambio_durante_calculo_no_republica_solucion_anterior(monkeypatch, falla_antigua):
    """El resultado reciente sobrevive al exito o fallo tardio del metodo anterior."""
    async def comprobar(vista, cliente):
        """Retiene el trabajador antiguo mientras termina el metodo vigente."""
        vista.cuadricula.cargar_datos([["2"]], ["1"])
        inicio, liberar = bloquear_primera_solicitud(monkeypatch, falla_antigua)
        boton = ui.button("Resolver prueba")
        antigua = asyncio.create_task(vista.resolver_sistema(boton))
        await inicio.wait()
        for metodo in ("gauss-jordan", "gauss", "gauss-jordan"):
            vista.pestanas_metodo.set_value(metodo)
        assert vista.ultimo_resultado is None
        await vista.resolver_sistema(boton)
        resultado = vista.ultimo_resultado
        assert resultado["solucion"] == ["1/2"]
        assert vista.historial[0]["metodo"] == "gauss-jordan"
        liberar.set()
        await antigua
        assert vista.ultimo_resultado is resultado
        assert len(vista.historial) == 1
        assert boton._props["loading"] == "false"
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))
