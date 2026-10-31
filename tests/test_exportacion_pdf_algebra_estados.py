"""Estados límite de vectores e inversas con regiones reales listas para captura."""
import asyncio

import pytest
from nicegui import ui
from src.frontend.controladores.exportacion_pdf.documento import generar_pdf
from tests.comun_exportacion_pdf import PORTADA, crear_captura
from tests.comun_exportacion_algebra import construir_algebra, regiones_control


@pytest.mark.parametrize('operacion,datos,estado', [
    ('suma_resta', [['1', '2', '3'], ['3', '2', '1']], 'EXITO'),
    ('escalar', [['1', '2', '3']], 'EXITO'),
    ('independencia', [['1', '0', '0']], 'EXITO'),
    ('combinacion_lineal', [['1', '0', '0'], ['0', '1', '0']], 'SIN_SOLUCION'),
    ('combinacion_lineal', [['1', '0', '0'], ['1', '0', '0']], 'UNICA'),
    ('combinacion_lineal', [['0', '0', '0'], ['0', '0', '0']], 'INFINITA'),
    ('suma_resta', [['1/0', '0', '0'], ['1', '0', '0']], 'ERROR'),
])
def test_operaciones_vectoriales_no_capturan_regiones_vacias(monkeypatch, operacion, datos, estado):
    """Coeficientes ausentes, independencia y errores conservan regiones y acciones correctas."""
    async def comprobar(vista, cliente):
        """Calcula cada operación y valida el documento desde su marcado real."""
        vista.pestanas.set_value(operacion)
        for vector, valores in zip(vista.panel_vectorial.vectores.values(), datos):
            vector['celdas'] = dict(enumerate(valores))
        await vista.calcular()
        assert vista.resultado_actual['estado'] == estado
        if estado == 'ERROR':
            assert not any(isinstance(elemento, ui.button) and elemento.text == 'Exportar PDF'
                           for elemento in cliente.elements.values())
            return
        control = vista.actualizar_exportacion_pdf.__self__
        regiones = regiones_control(control)
        assert all(list(region) for region in regiones)
        claves = [region._props['data-pdf-captura'] for region in regiones]
        assert 'vectores-resumen' in claves and 'vectores-procedimiento' in claves
        documento, _ = generar_pdf('vectores', PORTADA, vista.resultado_actual, [crear_captura(clave) for clave in claves])
        assert documento.startswith(b'%PDF-') and control.boton.visible
    asyncio.run(construir_algebra(monkeypatch, 'vectores', comprobar))


@pytest.mark.parametrize('datos,estado', [([['1', '2'], ['2', '4']], 'SINGULAR'), ([['1/0']], 'ERROR')])
def test_inversa_singular_exporta_y_error_no(monkeypatch, datos, estado):
    """La singularidad es un resultado documentable; un error de entrada no ofrece PDF."""
    async def comprobar(vista, cliente):
        """Invierte la captura y comprueba la disponibilidad del control."""
        vista.panel_matriz_cuadrada.cargar_matriz(datos)
        await vista.calcular(ui.button('Invertir prueba'))
        assert vista.ultimo_resultado['estado'] == estado
        botones = [elemento for elemento in cliente.elements.values()
                   if isinstance(elemento, ui.button) and elemento.text == 'Exportar PDF']
        assert bool(botones) is (estado == 'SINGULAR')
        if botones:
            assert botones[0].visible
    asyncio.run(construir_algebra(monkeypatch, 'inversa', comprobar))
