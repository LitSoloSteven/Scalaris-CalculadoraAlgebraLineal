"""Contratos del selector exclusivo y conservación de las capturas vectoriales."""
import asyncio
from pathlib import Path
from unittest.mock import Mock

import pytest
from nicegui import ui
from src.frontend.componentes.selector_opciones import SelectorOpciones
from src.frontend.textos import OPCIONES_OPERACIONES_VECTORES
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste


def test_opciones_y_regiones_conservan_contrato(monkeypatch):
    """Cada opción tiene nombre completo y controla una región persistente."""
    async def comprobar(vista, cliente):
        """Recorre las cuatro operaciones y descarta resultados sin borrar capturas."""
        selector = vista.pestanas
        assert isinstance(selector, SelectorOpciones)
        assert selector._props['role'] == 'radiogroup'
        assert selector._props['aria-label'] == 'Operaciones con vectores'
        assert 'pestanas-metodo' in selector.classes
        assert len(selector.botones) == 4
        vista.panel_suma_resta.vectores['u']['celdas'][0] = '1/1001'
        for valor, etiqueta, nombre in OPCIONES_OPERACIONES_VECTORES:
            vista.resultado_actual = {'estado': 'EXITO'}
            vista._huella_resultado = 'huella anterior'
            selector.set_value(valor)
            boton = selector.botones[valor]
            assert boton._props['aria-label'] == nombre and boton.text == etiqueta
            assert boton._props['aria-checked'] == 'true' and boton._props['tabindex'] == '0'
            assert sum(otro._props['tabindex'] == '0' for otro in selector.botones.values()) == 1
            region = next(elemento for elemento in cliente.elements.values()
                          if elemento.html_id == boton._props['aria-controls'])
            assert region._props['role'] == 'region'
            assert region._props['aria-labelledby'] == boton.html_id and region.visible
            assert vista.operacion_activa == valor
            if valor != 'suma_resta':
                assert vista.resultado_actual is None and vista._huella_resultado is None
        selector.set_value('suma_resta')
        assert vista.panel_suma_resta.vectores['u']['celdas'][0] == '1/1001'
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))


def test_selector_reutilizable_y_etiquetas_extensas(monkeypatch):
    """Dos selectores independientes no comparten valores, nombres ni regiones."""
    async def comprobar(vista, cliente):
        """Usa valores ajenos a la vista y texto hostil sin interpretar HTML."""
        notificar = Mock()
        def recibir(evento):
            """Conserva el valor notificado por el componente independiente."""
            notificar(evento.value)
        opciones = [('primera', '<script>' + 'Etiqueta ' * 100, 'Primera opción completa'),
                    ('segunda', 'Segunda', 'Segunda opción completa')]
        selector = SelectorOpciones(opciones, 'primera', recibir, 'Método independiente')
        assert selector.botones['primera'].text.startswith('<script>')
        assert not any(isinstance(elemento, ui.html) for elemento in selector.descendants())
        assert notificar.call_count == 0
        selector.set_value('segunda')
        notificar.assert_called_once_with('segunda')
        assert vista.operacion_activa == 'suma_resta'
        assert selector.value == 'segunda'
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))


@pytest.mark.parametrize('opciones,inicial', [([], 'ninguna'), ([('a', 'A', 'A')], 'b'),
                                             ([('a', 'A', 'A'), ('a', 'B', 'B')], 'a')])
def test_selector_rechaza_configuraciones_ambiguas(opciones, inicial):
    """No construye grupos vacíos ni selecciones sin una correspondencia única."""
    with pytest.raises(ValueError):
        SelectorOpciones(opciones, inicial, Mock(), 'Opciones')


@pytest.mark.parametrize('tema', ['papel', 'marea', 'medianoche'])
def test_contraste_calculado_del_selector(tema):
    """Los colores de texto y foco superan WCAG AA en los tres temas."""
    tokens = analizar_tokens('src/frontend/recursos/css/tokens.css')[tema]
    pares = [('text-sec', 'bg-panel', 4.5), ('btn-primary-text', 'btn-primary-bg', 4.5),
             ('focus-ring', 'bg-panel', 3), ('btn-primary-text', 'btn-primary-bg', 3)]
    for frente, fondo, minimo in pares:
        contraste = razon_contraste(hexadecimal_a_rgb(tokens[f'--{frente}']),
                                   hexadecimal_a_rgb(tokens[f'--{fondo}']))
        assert contraste >= minimo, (tema, frente, fondo, contraste)


def test_selector_reemplaza_scroll_y_respeta_movimiento():
    """Las reglas antiguas desaparecen y la adaptación pertenece al contenedor."""
    raiz = Path('src/frontend')
    controles = (raiz / 'vistas/operaciones_vectores/controles.py').read_text(encoding='utf-8')
    estilos = (raiz / 'recursos/css/vistas_vectores.css').read_text(encoding='utf-8')
    selector = (raiz / 'recursos/css/selector_opciones.css').read_text(encoding='utf-8')
    for anterior in ['pestanas-vectores', 'q-tabs__arrow', 'q-tabs--scrollable', 'q-tabs__content']:
        assert anterior not in controles + estilos + selector
    assert 'mobile-arrows' not in controles and 'outside-arrows' not in controles
    assert '@container selector-opciones' in selector and 'repeat(2, minmax(0, 1fr))' in selector
    assert '@media (prefers-reduced-motion: reduce)' in selector
    assert 'html[data-entrada="teclado"]' in selector
    assert '@layer quasar_importants' in selector
    assert 'scale(0.97)' in selector and 'text-overflow' not in selector
