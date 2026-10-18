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
        """Comprueba apertura, tarjeta canónica y ausencia del menú retirado."""
        assert vista.glosa_abierta is abrir
        assert codigos == (["abrir"] if abrir else [])
        tarjetas = [elemento for elemento in cliente.elements.values()
                    if "inicio-tarjeta" in elemento.classes]
        assert any(elemento._props.get("href") == "/algebra-lineal/determinantes" for elemento in tarjetas)
        assert not any(isinstance(elemento, ui.menu_item) for elemento in cliente.elements.values())

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar, {"glosa": "1" if abrir else ""}))
