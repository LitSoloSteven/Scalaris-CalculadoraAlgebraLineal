"""Las ayudas de limpieza siguen el identificador DOM estable de su control."""
import asyncio

import pytest
from nicegui import ui
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("herramienta", ["sistemas", "inversa"])
def test_ayuda_limpieza_apunta_al_identificador_publico(monkeypatch, herramienta):
    """Evita anclas cNN inexistentes cuando se personaliza el id del botón."""
    async def comprobar(vista, cliente):
        """Inspecciona los elementos reales del control y su ayuda emergente."""
        botones = [elemento for elemento in cliente.elements.values()
                   if isinstance(elemento, ui.button) and elemento._props.get("id") == "boton-limpiar-principal"]
        assert len(botones) == 1
        ayudas = [elemento for elemento in botones[0].descendants()
                  if isinstance(elemento, ui.tooltip)]
        assert len(ayudas) == 1
        assert ayudas[0]._props["target"] == "#boton-limpiar-principal"
        assert botones[0]._props["aria-label"] == "Limpiar"
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
