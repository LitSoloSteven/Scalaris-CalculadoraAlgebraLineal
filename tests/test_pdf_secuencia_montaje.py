"""Capturas temporales con vistas y cuerpos reales, sin modificar el reproductor."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.componentes.exportacion_pdf.entrada import renderizar_entrada
from src.frontend.componentes.exportacion_pdf.secuencia import preparar_secuencia
from tests.comun_exportacion_algebra import HERRAMIENTAS, calcular_algebra, construir_algebra
from tests.comun_exportacion_utilidades import CASOS, calcular_utilidad, construir_utilidad


def _comprobar_montaje(control, cliente):
    """Verifica aislamiento, contenido y retirada de las regiones de una herramienta."""
    vista = control.enlace.vista
    reproductor = getattr(vista, 'reproductor_pasos', None) or getattr(vista, 'reproductor', None)
    indice = reproductor.indice_actual if reproductor else None
    elementos = set(cliente.elements)
    with preparar_secuencia(control.herramienta, control.enlace) as temporal:
        regiones = [elemento for elemento in temporal.descendants() if 'data-pdf-captura' in elemento._props]
        claves = [region._props['data-pdf-captura'] for region in regiones]
        assert claves[0] == f'{control.herramienta}-entrada'
        assert len(claves) == len(set(claves))
        assert sum('-paso-' in clave for clave in claves) <= 3
        assert all(list(region.descendants()) for region in regiones)
        if reproductor:
            assert reproductor.indice_actual == indice
    assert temporal.is_deleted
    assert set(cliente.elements) == elementos


@pytest.mark.parametrize('herramienta', HERRAMIENTAS)
def test_secuencia_algebra_con_cuerpos_reales(monkeypatch, herramienta):
    """Cada herramienta reutiliza su renderizador sin dejar elementos ni cambiar el índice."""
    async def comprobar(vista, cliente):
        await calcular_algebra(herramienta, vista)
        _comprobar_montaje(vista.actualizar_exportacion_pdf.__self__, cliente)
    asyncio.run(construir_algebra(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize('caso', CASOS)
def test_secuencia_utilidades_y_escenas(monkeypatch, caso):
    """Las utilidades incluyen su entrada y las escenas no inventan un procedimiento."""
    async def comprobar(vista, cliente):
        await calcular_utilidad(caso, vista)
        _comprobar_montaje(vista.actualizar_exportacion_pdf.__self__, cliente)
    asyncio.run(construir_utilidad(monkeypatch, caso, comprobar))


def test_datos_html_se_escapan_en_tablas_y_etiquetas():
    """Una entrada con símbolos HTML conserva su texto sin crear etiquetas ejecutables."""
    with ui.column() as contenedor:
        renderizar_entrada({'matrices': {'A': {(0, 0): '<img src=x onerror=alert(1)>'}},
                            'expresion': '<script>prueba</script>'}, 'matrices')
    tablas = [elemento.content for elemento in contenedor.descendants() if isinstance(elemento, ui.html)]
    assert len(tablas) == 1
    assert '&lt;img' in tablas[0] and '<img' not in tablas[0]
    assert any(isinstance(elemento, ui.label) and elemento.text == '<script>prueba</script>'
               for elemento in contenedor.descendants())
    contenedor.delete()
