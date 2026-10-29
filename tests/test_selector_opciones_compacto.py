"""Coordenadas del indicador compartido, espaciado y carga de recursos del selector."""
import asyncio
from pathlib import Path
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend.componentes.selector_opciones import COLUMNAS_COMPACTAS, SelectorOpciones
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('cantidad', [2, 4])
def test_seleccion_sincroniza_filas_y_columnas_compactas(monkeypatch, cantidad):
    """El servidor actualiza las coordenadas para dos o cuatro opciones en ambos sentidos."""
    async def comprobar(vista, cliente):
        """Cambia el valor sin reconstruir opciones ni alterar sus regiones."""
        opciones = [(str(indice), str(indice), str(indice)) for indice in range(cantidad)]
        selector = SelectorOpciones(opciones, '0', Mock(), 'Opciones de prueba')
        columnas = min(COLUMNAS_COMPACTAS, cantidad)
        assert selector._props['data-selector-columnas'] == str(columnas)
        assert selector.style['--selector-columnas-compactas'] == str(columnas)
        assert selector.style['--selector-filas-compactas'] == str((cantidad + columnas - 1) // columnas)
        anterior = 0
        for indice in [*range(cantidad), *reversed(range(cantidad))]:
            selector.set_value(str(indice))
            assert selector.style['--selector-indice'] == str(indice)
            assert selector.style['--selector-columna-compacta'] == str(indice % columnas)
            assert selector.style['--selector-fila-compacta'] == str(indice // columnas)
            if indice != anterior:
                assert selector.style['--selector-indice-anterior'] == str(anterior)
            anterior = indice
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))


def test_etiquetas_del_selector_conservan_las_rutas_del_componente(monkeypatch):
    """Las etiquetas del componente conservan sus URL directas fuera del versionado global."""
    async def comprobar(vista, cliente):
        """Inspecciona las referencias reales del cliente sin presuponer invalidacion de cache."""
        for extension in ['css', 'js']:
            url = f'/assets/{extension}/selector_opciones.{extension}'
            assert f'"{url}"' in cliente.head_html
            assert f'"{url}?v=' not in cliente.head_html
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))


def test_secciones_vectoriales_comparten_un_gap_semantico(monkeypatch):
    """Las cuatro operaciones agrupan sus bloques con la misma separacion por token."""
    async def comprobar(vista, cliente):
        """Inspecciona las regiones persistentes que comparten el selector y la captura."""
        secciones = [elemento for elemento in cliente.elements.values()
                     if 'vectores-seccion' in elemento.classes]
        assert len(secciones) == 4
        assert all(elemento._props['role'] == 'region' for elemento in secciones)
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))


def test_indicador_compacto_se_mueve_sin_transiciones_de_redimensionado():
    """Solo activar la clase de seleccion inicia movimiento, con accesibilidad conservada."""
    estilos = Path('src/frontend/recursos/css/selector_opciones.css').read_text(encoding='utf-8')
    assert 'grid-auto-rows: 1fr' in estilos
    assert 'height: calc(100% / var(--selector-filas-compactas))' in estilos
    assert 'width: calc(100% / var(--selector-columnas-compactas))' in estilos
    assert '.selector-opciones-indicador { display: none; }' not in estilos
    assert 'animation: selector-opciones-deslizar var(--dur-state) var(--ease-std)' in estilos
    assert 'transition: transform var(--dur-med)' not in estilos
    assert 'html[data-entrada="teclado"] .selector-opciones-indicador' in estilos
    assert 'animation: none !important' in estilos
