"""Captura por filas y sincronización de los dos métodos iterativos."""
import asyncio

from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


def test_captura_iterativa_edita_filas_y_convierte_el_sistema(monkeypatch):
    """Comprueba campos numerados, límites, conversión y limpieza del borrador."""
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))

    async def _comprobar(vista, _cliente):
        captura = vista.captura
        captura.selector.set_value('ecuaciones')
        editor = captura.ecuaciones
        primera, segunda, tercera = editor.entradas
        assert isinstance(primera, ui.input) and not isinstance(primera, ui.textarea)
        assert segunda.props.get('aria-label') == 'Ecuación 2'
        primera.set_value('2x + y = 5')
        segunda.set_value('x + 2y = 4')
        tercera.set_value('dato sin signo igual')
        captura.selector.set_value('matriz')
        assert captura.selector.value == 'ecuaciones'
        assert tercera.value == 'dato sin signo igual'
        await editor.cambiar_cantidad(-1)
        assert editor.value == '2x + y = 5\nx + 2y = 4'
        captura.selector.set_value('matriz')
        assert captura.obtener()['matriz_a'] == [['2', '1'], ['1', '2']]
        captura.selector.set_value('ecuaciones')
        await vista.resolver()
        assert vista.ultimo_resultado['variables'] == ['x', 'y']
        vista.selector_metodo.set_value('gauss-seidel')
        assert editor.value == '2x + y = 5\nx + 2y = 4'
        await vista.resolver()
        assert vista.ultimo_resultado['metodo'] == 'gauss-seidel'
        for _ in range(DIMENSION_MAXIMA_SISTEMAS):
            await editor.cambiar_cantidad(1)
        assert len(editor.entradas) == DIMENSION_MAXIMA_SISTEMAS
        assert vista.ultimo_resultado is None
        captura.restablecer()
        assert editor.value == ''

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', _comprobar))
