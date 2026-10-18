"""Apertura pública de Glosa y accesos avanzados desde la página inicial."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("abrir", [False, True])
def test_parametro_publico_abre_solo_cuando_se_solicita(monkeypatch, abrir):
    """El constructor consume glosa=1 y mantiene el panel cerrado por defecto."""
    codigos = []
    destinos = []
    monkeypatch.setattr(ui.navigate, "to", destinos.append)
    monkeypatch.setattr("src.frontend.componentes.panel_ia.PanelIA.abrir",
                        lambda instancia: codigos.append("abrir"))

    async def comprobar(vista, cliente):
        """Comprueba apertura y accesos sin modificar el catálogo principal."""
        assert vista.glosa_abierta is abrir
        assert codigos == (["abrir"] if abrir else [])
        etiquetas = {"Determinante", "Modelo de Leontief", "Transformaciones lineales"}
        entradas = [elemento for elemento in cliente.elements.values()
                    if isinstance(elemento, ui.menu_item) and any(
                        isinstance(hijo, ui.item_section) and hijo.text in etiquetas for hijo in elemento.descendants())]
        assert len(entradas) == 3
        for entrada in entradas:
            for evento in entrada._event_listeners.values():
                if evento.type == "click":
                    evento.handler(None)
        assert destinos == ["/algebra-lineal/matrices?operacion=determinante",
                            "/algebra-lineal/leontief", "/algebra-lineal/transformaciones"]

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar, {"glosa": "1" if abrir else ""}))
