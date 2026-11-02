"""Captura y cálculo sin paneles auxiliares en matrices y vectores."""
import asyncio

import pytest
from nicegui import ui

from src.frontend import textos
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_calculos_vistas import calcular_minimo


@pytest.mark.parametrize("herramienta", ["matrices", "vectores"])
def test_captura_y_resultado_conservan_disposicion_sin_previa_ni_historial(monkeypatch, herramienta):
    """Retirar los paneles no altera el cálculo exacto ni la invalidación al editar."""
    async def comprobar(vista, cliente):
        """Monta los dos paneles principales y comprueba sus estados antes y después de editar."""
        paneles = [elemento for elemento in cliente.elements.values()
                   if 'disposicion-dividida' in elemento._classes]
        assert len(paneles) == 1
        assert len(paneles[0].default_slot.children) == 2
        expansiones = [elemento._props.get('label') for elemento in cliente.elements.values()
                       if isinstance(elemento, ui.expansion)]
        assert textos.MODELOS_VISTA_PREVIA not in expansiones
        assert textos.MODELOS_HISTORIAL not in expansiones
        assert not hasattr(vista, 'sesion_capturas')
        await calcular_minimo(herramienta, vista)
        if herramienta == "matrices":
            vista.entrada_expresion.set_value("A - A")
        else:
            vista.panel_vectorial.vectores["u"]["celdas"][0] = "99"
            vista.panel_vectorial.vectores["u"]["orientacion"] = "fila"
            vista._al_cambiar_vectores()
        assert (vista.ultimo_resultado if herramienta == "matrices" else vista.resultado_actual) is None
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
