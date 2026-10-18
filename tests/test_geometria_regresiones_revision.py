"""Regresiones de celdas, transferencias y trazas señaladas por revisión independiente."""
import json
from unittest.mock import MagicMock
from nicegui import ui

from src.frontend.vistas.geometria.vista_geometria import VistaGeometria
from src.frontend.vistas.geometria._transferencia_geometria import _cargar_vectores
from src.frontend.vistas.geometria._figura_combinacion import construir_figura_combinacion
from src.frontend.controladores.geometria import ControladorGeometria, selector_celda_error


def _crear_controles(escena):
    vista = VistaGeometria()
    vista.escena = escena
    vista.contenedor_controles = ui.column()
    vista._construir_controles(escena)
    vista._programar_actualizacion = MagicMock()
    return vista


def test_error_en_vector_tras_eliminar_otro_enfoca_celda_existente():
    """El selector sigue la posición enviada al controlador aunque haya huecos de nombres."""
    vista = _crear_controles('combinacion')
    panel = vista.panel_combinacion
    panel.agregar_vector()
    panel.eliminar_vector('v_1')
    panel.vectores['v_2']['celdas'][0] = 'abc'
    resultado = ControladorGeometria.procesar_combinacion(json.dumps(vista._construir_carga()))
    assert resultado['estado'] == 'ERROR'
    selector = selector_celda_error(resultado['celda_error'], escena='combinacion')
    entradas = [elemento for elemento in panel.vectores['v_2']['contenedor'].descendants() if isinstance(elemento, ui.input)]
    identificador = entradas[0]._props['data-geometria-vector']
    assert selector == f'input[data-geometria-vector="{identificador}"][data-geometria-indice="0"]'
    vista.contenedor_controles.delete()


def test_transferencia_sincroniza_dimension_y_celdas():
    """La cabecera y las componentes reflejan la dimensión recibida."""
    vista = _crear_controles('vectores')
    panel = vista.panel_vectores
    assert panel.etiqueta_dimension.text == '3'
    _cargar_vectores(vista, [['1/3', '2'], ['4', '5']])
    assert panel.dimension == 2
    assert panel.etiqueta_dimension.text == '2'
    assert panel.boton_reducir_dimension.enabled
    assert panel.boton_aumentar_dimension.enabled
    entradas = [elemento for elemento in panel.vectores['u']['contenedor'].descendants() if isinstance(elemento, ui.input)]
    assert len(entradas) == 2
    assert entradas[0].value == '1/3'
    vista.contenedor_controles.delete()


def test_columnas_combinacion_3d_conservan_grosor_original():
    """Las líneas tridimensionales mantienen el grosor establecido de tres."""
    figura = construir_figura_combinacion({'numero_variables': 3, 'vectores': [{'aproximado': [1, 2, 3]}]})
    assert figura.data[0].line.width == 3
    assert figura.data[0].line.dash == 'dot'
