"""Montaje y ediciones reales de las herramientas algebraicas exportables."""
from types import SimpleNamespace

from nicegui import ui
from tests.comun_calculos_vistas import calcular_minimo
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina

HERRAMIENTAS = ('vectores', 'matrices', 'inversa', 'determinantes', 'factorizacion_lu', 'leontief', 'transformaciones')


async def construir_algebra(monkeypatch, herramienta, comprobar):
    """Monta también las rutas matriciales diferidas con el transporte común de pruebas."""
    monkeypatch.setitem(VISTAS_RUTAS, 'determinantes', ('operaciones_matrices.vista_determinante', 'VistaDeterminante'))
    monkeypatch.setitem(VISTAS_RUTAS, 'factorizacion_lu', ('operaciones_matrices.vista_factorizacion_lu', 'VistaFactorizacionLU'))
    await construir_pagina(monkeypatch, herramienta, comprobar)


async def calcular_algebra(herramienta, vista):
    """Calcula un ejemplo pequeño por el manejador real de cada vista."""
    if herramienta in ('determinantes', 'factorizacion_lu'):
        vista.panel_matriz.cargar_matriz([['2', '0'], ['0', '3']])
        await vista.calcular(SimpleNamespace(sender=ui.button('Calcular prueba')))
        assert vista.ultimo_resultado['estado'] == 'EXITO'
    else:
        await calcular_minimo(herramienta, vista)


def editar_algebra(herramienta, vista):
    """Cambia un dato a través del control o callback usado por la captura real."""
    if herramienta == 'vectores':
        next(iter(vista.panel_vectorial.vectores.values()))['celdas'][0] = '7'
        vista._al_cambiar_vectores()
    elif herramienta == 'matrices':
        vista.entrada_expresion.set_value('A + A + A')
    elif herramienta == 'inversa':
        vista.panel_matriz_cuadrada.cargar_matriz([['7', '0'], ['0', '3']])
    elif herramienta in ('factorizacion_lu', 'determinantes'):
        vista.panel_matriz.cargar_matriz([['7', '0'], ['0', '3']])
    elif herramienta == 'leontief':
        vista.entradas_demanda[0].set_value('7')
    else:
        vista.entradas_coeficientes[0][0].set_value('7')


def regiones_control(control):
    """Devuelve los elementos capturables del contenedor asociado al exportador."""
    contenedor = control.enlace.estado()[0]
    return [elemento for elemento in contenedor.descendants() if 'data-pdf-captura' in elemento._props]
