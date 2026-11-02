"""Cobertura de marcas numéricas y exclusión de texto libre en las páginas reales."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina


def _comprobar_texto_libre(vista, cliente, herramienta):
    for nombre in ('entradas_sectores', 'entradas_variables'):
        assert all(entrada._props.get('data-solo-numerico') == 'false'
                   for entrada in getattr(vista, nombre, []))
    if herramienta == 'vectores':
        assert vista.entrada_escalar._props['data-solo-numerico'] == 'true'
    if herramienta == 'matrices':
        assert 'data-solo-numerico' not in vista.entrada_expresion._props
    textos = [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.textarea)]
    assert all(elemento._props.get('data-solo-numerico') != 'true' for elemento in textos)


@pytest.mark.parametrize('herramienta', [
    'sistemas', 'vectores', 'matrices', 'inversa', 'determinantes',
    'leontief', 'transformaciones', 'bases', 'romanos',
])
def test_paginas_marcan_numeros_conservando_texto_libre(monkeypatch, herramienta):
    """Las páginas algebraicas marcan celdas; nombres, expresiones y utilidades quedan libres."""
    async def comprobar(vista, cliente):
        """Inspecciona los controles montados por la ruta y sus propiedades reales."""
        entradas = [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.input)]
        numericas = [entrada for entrada in entradas if entrada._props.get('data-solo-numerico') == 'true']
        assert bool(numericas) is (herramienta not in {'bases', 'romanos'})
        _comprobar_texto_libre(vista, cliente, herramienta)
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
