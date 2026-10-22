"""Acciones disponibles segun los limites de cantidad de las familias vectoriales."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('operacion', ['suma_resta', 'escalar'])
def test_familias_fijas_no_montan_acciones_de_cantidad(monkeypatch, operacion):
    """Las familias fijas conservan orientacion y dimension sin ofrecer anadir o borrar."""
    async def comprobar(vista, cliente):
        """Recorre transiciones y reconstrucciones sin necesitar un boton de anadir."""
        panel = vista.paneles[operacion]
        assert not panel.permite_variar_cantidad
        assert not hasattr(panel, 'boton_agregar_vector')
        assert not panel._botones_eliminar_vectores
        for cambio in [1, -1]:
            await panel.ajustar_dimension(cambio)
            panel._actualizar_botones_vectores()
            assert panel.boton_aumentar_dimension in panel._botones_transicion_vectores()
        for nombre in panel.vectores:
            assert panel.vectores[nombre]['boton_orientacion'] is not None
        panel.renderizar_todos_vectores()
        assert len(panel.vectores) == panel.minimo_vectores == panel.maximo_vectores
        assert not panel._botones_eliminar_vectores
        assert not any(isinstance(elemento, ui.button) and elemento.text == 'Añadir Vector'
                       for elemento in panel.contenedor_cabecera.descendants())
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))


@pytest.mark.parametrize('operacion', ['combinacion_lineal', 'independencia'])
def test_familias_variables_conservan_acciones_y_limites(monkeypatch, operacion):
    """Las acciones variables siguen disponibles y respetan minimo, maximo y objetivo."""
    async def comprobar(vista, cliente):
        """Anade y retira vectores hasta comprobar ambos extremos de la familia."""
        panel = vista.paneles[operacion]
        assert panel.permite_variar_cantidad
        assert panel.boton_agregar_vector.enabled
        assert panel._botones_eliminar_vectores
        assert all(not boton.enabled for boton in panel._botones_eliminar_vectores.values())
        if panel.etiqueta_fija_primer_vector:
            assert panel.etiqueta_fija_primer_vector not in panel._botones_eliminar_vectores
        while len(panel.vectores) < panel.maximo_vectores:
            panel.agregar_vector()
        assert not panel.boton_agregar_vector.enabled
        assert all(boton.enabled for boton in panel._botones_eliminar_vectores.values())
        nombre = next(iter(panel._botones_eliminar_vectores))
        panel.eliminar_vector(nombre)
        assert panel.boton_agregar_vector.enabled
        assert panel.boton_agregar_vector in panel._botones_transicion_vectores()
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))


def test_escena_vectores_hereda_la_ocultacion_de_acciones(monkeypatch):
    """El Visualizador conserva sus dos vectores sin ofrecer controles de cantidad."""
    async def comprobar(vista, cliente):
        """Comprueba el panel real de la escena y una transicion de dimension."""
        panel = vista.panel_vectores
        assert panel.minimo_vectores == panel.maximo_vectores == 2
        assert not panel.permite_variar_cantidad
        assert not hasattr(panel, 'boton_agregar_vector')
        assert not panel._botones_eliminar_vectores
        await panel.ajustar_dimension(1)
        assert len(panel.vectores) == 2
        assert panel.dimension == 4
        assert panel.boton_reducir_dimension in panel._botones_transicion_vectores()
    asyncio.run(construir_pagina(monkeypatch, 'visualizador', comprobar, {'escena': 'vectores'}))
