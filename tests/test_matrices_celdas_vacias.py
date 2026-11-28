"""Validación de operandos incompletos y recuperación al escribir cero."""

import asyncio

from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina


def test_celda_vacia_solo_bloquea_el_operando_utilizado(monkeypatch):
    """Señala la coordenada incompleta y recupera el cálculo con un cero explícito."""
    async def comprobar(vista, cliente):
        """Ejercita la evaluación desde la vista montada con su botón real."""
        vista.panel_captura_matrices.cargar_datos({'A': [['2', '']], 'B': [['']]})
        vista.entrada_expresion.set_value('A+A')
        boton = next(elemento for elemento in cliente.elements.values()
                     if isinstance(elemento, ui.button) and elemento.text == 'Evaluar')
        celda = vista.panel_captura_matrices.matrices['A']['entradas'][0][1]

        await vista.evaluar_expresion(boton)

        assert vista.ultimo_resultado is None
        assert celda.props.get('aria-invalid')
        assert any('A[1,2]' in elemento.text for elemento in vista.contenedor_resultados.descendants()
                   if isinstance(elemento, ui.label))
        assert not boton.props.get('loading')

        celda.set_value('0')
        await vista.evaluar_expresion(boton)

        assert not celda.props.get('aria-invalid')
        assert vista.ultimo_resultado['matriz_resultado']['datos'] == [['4', '0']]

    asyncio.run(construir_pagina(monkeypatch, 'matrices', comprobar))
