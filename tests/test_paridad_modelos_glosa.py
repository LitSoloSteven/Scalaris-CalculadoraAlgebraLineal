"""Paridad, vigencia y restauración de los modelos con controles reales."""
import asyncio
import copy

import pytest
from nicegui import ui

from src.frontend.controladores.operaciones_matrices.contexto_modelos import capturar_modelo
from src.frontend.vistas.operaciones_matrices.carga_modelos import cargar_captura_modelo
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_calculos_vistas import calcular_minimo


@pytest.mark.parametrize("herramienta", ["leontief", "transformaciones"])
def test_modelo_ofrece_glosa_fases_y_sesion_completa(monkeypatch, herramienta):
    """Un cálculo real ofrece ayuda, foco y restauración; editar retira el resultado."""
    async def comprobar(vista, cliente):
        """Ejercita cálculo, vista previa, historial e invalidación por una celda."""
        assert vista.panel_ia is not None
        assert vista.obtener_senales_ia().estado == "sin_resultado"
        await calcular_minimo(herramienta, vista)
        assert vista.obtener_contexto_ia().herramienta == herramienta
        assert vista.obtener_contexto_ia().resultado is not None
        assert vista.obtener_senales_ia().estado == "exito"
        reproductor = vista.reproductor_pasos
        assert reproductor.lineas_ayuda and len(reproductor.grupos) > 1
        assert all(paso.meta_explicar and paso.meta_explicar["detalle"]["formula"] for paso in reproductor.pasos)
        assert len(vista.historial) == 1
        captura = copy.deepcopy(vista.historial[0]["captura"])
        await vista.tarea_vista_previa
        assert any(isinstance(elemento, ui.html) for elemento in vista.contenedor_vista_previa.descendants())
        vista.entradas_coeficientes[0][0].set_value("incorrecto")
        assert vista.ultimo_resultado is None and vista.reproductor_pasos is None
        assert vista.obtener_contexto_ia().resultado is None
        assert vista.obtener_senales_ia().invalida.foco == (0, 0)
        cargar_captura_modelo(vista, captura)
        assert capturar_modelo(vista) == captura
        assert vista.ultimo_resultado is None and len(vista.historial) == 1
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
