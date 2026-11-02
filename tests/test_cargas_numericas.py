"""Cargas y pegados saneados en los consumidores reales de captura."""
import asyncio
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend.componentes.panel_matriz_cuadrada import PanelMatrizCuadrada
from src.frontend.componentes.panel_matriz_rectangular import PanelMatrizRectangular
from src.frontend.componentes.estado_captura_matrices import crear_registro_matriz
from src.frontend.componentes.captura_vectores import PanelCapturaVectores
from src.frontend.componentes.cuadricula_ecuaciones import CuadriculaEcuaciones


@pytest.mark.parametrize('rectangular', [False, True])
def test_cargar_matriz_filtra_sin_mover_celdas_ni_perder_fracciones(monkeypatch, rectangular):
    """El saneamiento conserva dimensiones y huecos, y publica una sola actualización."""
    monkeypatch.setattr(ui, 'notify', Mock())
    panel = PanelMatrizRectangular() if rectangular else PanelMatrizCuadrada()
    publicacion = Mock()
    setattr(panel, '_publicar' if rectangular else '_publicar_matriz', publicacion)
    datos = [['a1', 'letras'], ['-2/3', '0.25b']]
    panel.cargar_matriz(datos)
    assert panel.obtener_datos_matriz() == [['1', '0'], ['-2/3', '0.25']]
    assert datos[0][1] == 'letras'
    publicacion.assert_called_once_with()


@pytest.mark.parametrize('rectangular', [False, True])
@pytest.mark.parametrize('texto,esperado', [
    ('a1\tletras\n-2/3\t0.25b', [['1', '0'], ['-2/3', '0.25']]),
    ('1\t\n\t4', [['1', '0'], ['0', '4']]),
])
def test_pegar_portapapeles_sanea_sin_desplazar_celda_rechazada(monkeypatch, rectangular, texto, esperado):
    """Una celda de letras se vacía en su posición al pegar desde el botón Python."""
    monkeypatch.setattr(ui, 'notify', Mock())

    async def leer(_codigo):
        """Devuelve una tabla de prueba sin acceder al portapapeles del sistema."""
        return texto

    monkeypatch.setattr(ui, 'run_javascript', leer)
    panel = PanelMatrizRectangular() if rectangular else PanelMatrizCuadrada()
    setattr(panel, '_publicar' if rectangular else '_publicar_matriz', Mock())
    asyncio.run(panel.pegar_desde_portapapeles())
    assert panel.obtener_datos_matriz() == esperado


def test_registro_matriz_sanea_datos_sin_alterar_dimensiones(monkeypatch):
    """Las restauraciones de Matrices usan el mismo filtro antes de crear el caché."""
    monkeypatch.setattr(ui, 'notify', Mock())
    registro = crear_registro_matriz([['1a', 'letras', '-1/2']])
    assert (registro['filas'], registro['columnas']) == (1, 3)
    assert registro['cache'] == {(0, 0): '1', (0, 2): '-1/2'}


def test_carga_vectores_conserva_nombre_y_orientacion(monkeypatch):
    """Filtrar componentes no cambia las claves ni la orientación solicitada."""
    monkeypatch.setattr(ui, 'notify', Mock())
    panel = PanelCapturaVectores('prueba')
    panel.renderizar_todos_vectores = Mock()
    panel.cargar_datos({'u': ['a1', '-2/3b'], 'v_1': ['0.25', 'letras']}, 'fila')
    assert set(panel.vectores) == {'u', 'v_1'}
    assert panel.vectores['u']['celdas'] == {0: '1', 1: '-2/3'}
    assert panel.vectores['v_1']['celdas'] == {0: '0.25', 1: ''}
    assert all(vector['orientacion'] == 'fila' for vector in panel.vectores.values())


def test_carga_sistemas_filtra_coeficientes_y_terminos(monkeypatch):
    """Las dos partes de un sistema se filtran antes de reconstruir sus controles."""
    monkeypatch.setattr(ui, 'notify', Mock())
    cuadricula = CuadriculaEcuaciones()
    cuadricula.generar_cuadricula = Mock()
    cuadricula.cargar_datos([['1a', '-2/3'], ['letras', '+4']], ['5b', '0.25c'])
    assert cuadricula._cache_coeficientes == {(0, 0): '1', (0, 1): '-2/3', (1, 1): '+4'}
    assert cuadricula._cache_independientes == {0: '5', 1: '0.25'}
