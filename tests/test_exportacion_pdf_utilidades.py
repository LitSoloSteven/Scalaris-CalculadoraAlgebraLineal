"""Vigencia y entrega real del generador en utilidades y las tres escenas."""
import asyncio

import pytest
from nicegui import ui
from src.frontend.componentes.exportacion_pdf import boton as modulo_boton
from tests.comun_exportacion_algebra import regiones_control
from tests.comun_exportacion_pdf import PORTADA, crear_captura
from tests.comun_exportacion_utilidades import (
    CASOS, construir_utilidad, calcular_utilidad, editar_utilidad, herramienta_de,
)


def _comprobar_descendientes(regiones):
    descendientes = [hijo for region in regiones for hijo in region.descendants()]
    assert not any('data-pdf-captura' in hijo._props for hijo in descendientes)
    assert not any(hijo._props.get('aria-label') == 'Preguntas sugeridas' for hijo in descendientes)


@pytest.mark.parametrize('caso', CASOS)
def test_resultado_marca_regiones_y_oculta_exportacion_al_editar(monkeypatch, caso):
    """Un resultado real conserva identidad y pierde vigencia al editar o limpiar."""
    async def comprobar(vista, cliente):
        """Inspecciona los consumidores montados sin sustituir el exportador."""
        assert not any(isinstance(elemento, ui.button) and elemento.text == 'Exportar PDF'
                       for elemento in cliente.elements.values())
        await calcular_utilidad(caso, vista)
        control = vista.actualizar_exportacion_pdf.__self__
        assert control.boton.visible and control.enlace.vigente(control.resultado)
        regiones = regiones_control(control)
        claves = {elemento._props['data-pdf-captura'] for elemento in regiones}
        herramienta = herramienta_de(caso)
        esperada = 'visualizador-resumen' if herramienta == 'visualizador' else f'{herramienta}-resultado'
        assert esperada in claves
        assert len(claves) == len(regiones)
        _comprobar_descendientes(regiones)
        testigo = control.enlace.testigo()
        await editar_utilidad(caso, vista)
        assert not control.enlace.comprobar(testigo, control.resultado)
        vista.limpiar_todo()
        assert not control.enlace.vigente(control.resultado)
        assert control.boton.is_deleted or not control.boton.visible
    asyncio.run(construir_utilidad(monkeypatch, caso, comprobar))


def _trabajador(vista, control, caso, cambio):
    async def trabajar(funcion, *argumentos):
        """Genera el documento después de introducir la carrera indicada."""
        if funcion is not modulo_boton.generar_pdf:
            return funcion(*argumentos)
        if cambio == 'editar':
            await editar_utilidad(caso, vista)
        elif cambio == 'limpiar':
            vista.limpiar_todo()
        elif cambio == 'recalcular':
            if herramienta_de(caso) == 'visualizador':
                vista.ultimo_hash_entrada = None
            await calcular_utilidad(caso, vista)
        elif cambio == 'cerrar':
            control.dialogo.dialogo.close()
        return funcion(*argumentos)
    return trabajar


def _preparar_generacion(monkeypatch, vista):
    control = vista.actualizar_exportacion_pdf.__self__
    capturas = [crear_captura(region._props['data-pdf-captura']) for region in regiones_control(control)]
    control.abrir()
    for clave, valor in PORTADA.items():
        control.dialogo.campos[clave].set_value(valor)

    async def capturar(identificador):
        """Exige que el capturador cliente reciba la raíz DOM vigente."""
        assert identificador == control.enlace.raiz
        return capturas
    monkeypatch.setattr(modulo_boton, 'capturar_regiones', capturar)
    return control


@pytest.mark.parametrize('caso', CASOS)
@pytest.mark.parametrize('cambio', ('ninguno', 'editar', 'limpiar', 'recalcular', 'cerrar'))
def test_descarga_o_descarta_utilidad_segun_estado_real(monkeypatch, caso, cambio):
    """El generador real entrega exclusivamente la solicitud aún visible y vigente."""
    async def comprobar(vista, cliente):
        """Sustituye solo navegador y transporte de descarga, conservando el PDF real."""
        await calcular_utilidad(caso, vista)
        control = _preparar_generacion(monkeypatch, vista)
        descargas = []
        monkeypatch.setattr(ui, 'download', lambda *argumentos, **opciones: descargas.append((argumentos, opciones)))
        monkeypatch.setattr(modulo_boton.run, 'io_bound', _trabajador(vista, control, caso, cambio))
        await control.generar()
        assert len(descargas) == int(cambio == 'ninguno')
        assert not control.ocupado
        if descargas:
            assert descargas[0][0][0].startswith(b'%PDF-')
            assert descargas[0][1]['filename'].isascii()
    asyncio.run(construir_utilidad(monkeypatch, caso, comprobar))
