"""Precisión visible, valores extremos y vigencia del resultado al cambiar el formato."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.controladores.algebra.sistemas_lineales.resolucion.presentacion_iterativa import (
    FORMATO_EXACTO, presentar_numero_iterativo,
)
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


@pytest.mark.parametrize(('exacto', 'decimales', 'esperado'), [
    ('1/3', 2, '0.33'),
    ('1/10', 4, '0.1000'),
    ('2/3', 0, '1'),
    ('-1/900', 2, '-1.11e-3'),
    ('0', 2, '0.00'),
    ('1/' + '9' * 5000, 2, '1.00e-5000'),
    ('1' + '0' * 5000, 2, '1.00e+5000'),
    ('1/3', None, '1/3'),
])
def test_presentacion_iterativa_redondea_sin_perder_orden_de_magnitud(exacto, decimales, esperado):
    """Visualiza enteros, fracciones y magnitudes extremas sin tocar el valor original."""
    assert presentar_numero_iterativo(exacto, decimales) == esperado


def test_selector_representa_el_resultado_vigente_sin_recalcular(monkeypatch):
    """Refresca tabla y paso seleccionado con el formato elegido y retira la exportación anterior."""
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))

    async def _comprobar(vista, _cliente):
        vista.captura.restablecer(True)
        await vista.resolver()
        resultado = vista.ultimo_resultado
        vector = resultado['pasos'][2]['vector_nuevo']
        vista.reproductor_pasos.ir_a(2)
        exportacion = vista.actualizar_exportacion_pdf.__self__
        assert vista.selector_decimales.value == 2
        assert '0.62' in _etiquetas(vista.contenedor_resultados)
        vista.selector_decimales.set_value(4)
        assert '0.6250' in _etiquetas(vista.contenedor_resultados)
        assert vista.ultimo_resultado is resultado
        assert vista.reproductor_pasos.indice_actual == 2
        assert vista.reproductor_pasos.pasos[2].cuerpo[0]['vector_nuevo'] == vector
        assert not exportacion.enlace.vigente(exportacion.resultado)
        vista.selector_decimales.set_value(FORMATO_EXACTO)
        assert '5/8' in _etiquetas(vista.contenedor_resultados)
        assert vista.reproductor_pasos.indice_actual == 2

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', _comprobar))


def _etiquetas(contenedor) -> list[str]:
    return [elemento.text for elemento in contenedor.descendants() if isinstance(elemento, ui.label)]
