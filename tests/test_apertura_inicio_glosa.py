"""Apertura pública de Glosa y acceso directo a Determinantes desde el inicio."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("abrir", [False, True])
def test_parametro_publico_abre_solo_cuando_se_solicita(monkeypatch, abrir):
    """El constructor consume glosa=1 y mantiene el panel cerrado por defecto."""
    codigos = []
    monkeypatch.setattr("src.frontend.componentes.panel_ia.PanelIA.abrir",
                        lambda instancia: codigos.append("abrir"))

    async def comprobar(vista, cliente):
        """Comprueba apertura, enlace canónico y ausencia del menú retirado."""
        assert vista.glosa_abierta is abrir
        assert codigos == (["abrir"] if abrir else [])
        enlaces = [elemento for elemento in cliente.elements.values()
                   if "inicio-enlace" in elemento.classes]
        assert any(elemento._props.get("href") == "/algebra-lineal/determinantes" for elemento in enlaces)
        menus = [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.menu_item)]
        assert {elemento._props.get("data-tema-opcion") for elemento in menus} == {"papel", "marea", "medianoche"}

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar, {"glosa": "1" if abrir else ""}))
