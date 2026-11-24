"""Exportación PDF, secuencia documental y vigencia en iterativos y subespacios."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.componentes.exportacion_pdf.montaje import boton as modulo_boton
from src.frontend.componentes.exportacion_pdf.montaje.secuencia import preparar_secuencia
from src.frontend.controladores.exportacion_pdf.documento.documento import generar_pdf
from src.frontend.controladores.exportacion_pdf.documento.figuras import preparar_figuras
from src.frontend.nucleo.textos import textos
from src.frontend.presentacion import tema
from src.frontend.presentacion.recursos_vistas import seleccionar_recursos
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.comun_exportacion_algebra import regiones_control
from tests.comun_exportacion_pdf import PORTADA, crear_captura


@pytest.fixture(autouse=True)
def registrar_vistas_nuevas(monkeypatch):
    """Registra las rutas nuevas para las pruebas de exportación PDF."""
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))
    monkeypatch.setitem(VISTAS_RUTAS, 'espacios_subespacios', (
        'algebra.operaciones_vectores.vista_espacios_subespacios', 'VistaEspaciosSubespacios',
    ))


def _botones_pdf(cliente) -> list[ui.button]:
    return [
        elemento for elemento in cliente.elements.values()
        if isinstance(elemento, ui.button) and elemento.text == textos.PDF_EXPORTAR
    ]


def _claves_validas(control, herramienta: str) -> list[str]:
    regiones = regiones_control(control)
    claves = [region._props['data-pdf-captura'] for region in regiones]
    assert len(claves) == len(set(claves))
    assert f'{herramienta}-resumen' in claves
    assert all(list(region) for region in regiones)
    assert not any('data-pdf-captura' in ancestro._props for region in regiones for ancestro in region.ancestors())
    return claves


def test_registro_y_recursos_pdf_de_ambas_herramientas():
    """Registra ambas herramientas y entrega estilos y capturador PDF por vista."""
    for herramienta in ('metodos_iterativos', 'espacios_subespacios'):
        assert herramienta in textos.PDF_HERRAMIENTAS
        assert herramienta in textos.PDF_REGIONES_POR_HERRAMIENTA
        assert herramienta in textos.PDF_ESTADOS_POR_HERRAMIENTA
        cabecera = seleccionar_recursos(tema._CABECERA_HTML, herramienta)
        assert '/assets/js/herramientas/documentos/captura_pdf.js' in cabecera
        assert '/assets/js/herramientas/documentos/clon_pdf.js' in cabecera
        assert '/assets/css/utilidades/exportacion_pdf.css' in cabecera


@pytest.mark.parametrize('metodo', ['jacobi', 'gauss-seidel'])
def test_pdf_iterativos_secuencia_y_cero_barridos(monkeypatch, metodo):
    """Exporta ejemplo completo con tabla y secuencia y maneja cero barridos y errores."""
    async def comprobar(vista, cliente):
        """Comprueba montaje completo, secuencia temporal, cero barridos y diagonal nula."""
        vista.captura.restablecer(True)
        await vista.resolver()
        control = vista.actualizar_exportacion_pdf.__self__
        assert sum(boton.visible for boton in _botones_pdf(cliente)) == 1
        claves = _claves_validas(control, 'metodos_iterativos')
        assert {'metodos_iterativos-resumen', 'metodos_iterativos-tabla', 'metodos_iterativos-procedimiento'} == set(claves)
        with preparar_secuencia('metodos_iterativos', control.enlace) as temporal:
            indice_antes = vista.reproductor_pasos.indice_actual
            secuencia = [
                elemento._props['data-pdf-captura']
                for elemento in temporal.descendants()
                if 'data-pdf-captura' in elemento._props
            ]
            assert secuencia[0] == 'metodos_iterativos-entrada'
            assert 'metodos_iterativos-resultado' in secuencia
        assert temporal.is_deleted
        assert vista.reproductor_pasos.indice_actual == indice_antes
        documento, _ = generar_pdf('metodos_iterativos', PORTADA, control.resultado, [crear_captura(clave) for clave in claves])
        assert documento.startswith(b'%PDF-')
        assert b'Ana de Prueba' in documento
        vista.captura.selector.set_value('ecuaciones')
        vista.captura.ecuaciones.set_value('x = 1')
        vista.captura._campos_vector()[0].set_value('1')
        await vista.resolver()
        control_cero = vista.actualizar_exportacion_pdf.__self__
        assert _claves_validas(control_cero, 'metodos_iterativos') == ['metodos_iterativos-resumen']
        vista.captura.ecuaciones.set_value('0x = 1')
        await vista.resolver()
        assert vista.actualizar_exportacion_pdf is None

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar, {'method': metodo}))


def _configurar_caso_subespacios(vista, caso: str) -> None:
    """Prepara la captura de subespacios según el escenario de prueba."""
    if caso == 'generadores_3d':
        vista.captura.cargar_ejemplo()
        return
    vista.selector_modo.set_value('restricciones')
    vista.captura.selector.set_value('ecuaciones')
    if caso == 'afin_3d':
        vista.captura.ecuaciones.set_value('-x1 - x2 + x3 = 1')
    elif caso == 'vacio':
        vista.captura.establecer_dimension_ambiente(2)
        vista.captura.ecuaciones.set_value('x = 0\nx = 1')
    else:
        vista.captura.establecer_dimension_ambiente(4)
        vista.captura.ecuaciones.set_value('x1 + x4 = 0')


@pytest.mark.parametrize('caso', ['generadores_3d', 'afin_3d', 'vacio', 'dimension_4'])
def test_pdf_subespacios_regiones_pruebas_y_grafica(monkeypatch, caso):
    """Exporta pruebas, omite gráfica en vacío o ℝ⁴ y marca Plotly en 1D a 3D."""
    async def comprobar(vista, cliente):
        """Configura el escenario y valida regiones, secuencia temporal y PDF."""
        _configurar_caso_subespacios(vista, caso)
        await vista.analizar()
        control = vista.actualizar_exportacion_pdf.__self__
        claves = _claves_validas(control, 'espacios_subespacios')
        espera_grafica = caso in ('generadores_3d', 'afin_3d')
        assert ('espacios_subespacios-grafica' in claves) is espera_grafica
        if espera_grafica:
            nodo_grafica = next(
                elemento for elemento in vista.contenedor_resultados.descendants()
                if elemento._props.get('data-pdf-captura') == 'espacios_subespacios-grafica'
            )
            assert nodo_grafica._props.get('data-pdf-motor') == 'plotly'
        indice_antes = vista.reproductor_pasos.indice_actual
        with preparar_secuencia('espacios_subespacios', control.enlace) as temporal:
            secuencia = [
                elemento._props['data-pdf-captura']
                for elemento in temporal.descendants()
                if 'data-pdf-captura' in elemento._props
            ]
        assert temporal.is_deleted
        assert vista.reproductor_pasos.indice_actual == indice_antes
        assert secuencia[0] == 'espacios_subespacios-entrada'
        assert 'espacios_subespacios-pruebas' in secuencia
        capturas = [crear_captura(clave) for clave in claves]
        figuras = preparar_figuras('espacios_subespacios', control.resultado, capturas)
        assert len(figuras) == (5 if espera_grafica else 4)
        assert any(figura['imagen'].clave == 'espacios_subespacios-grafica' for figura in figuras) is espera_grafica
        documento, _ = generar_pdf('espacios_subespacios', PORTADA, control.resultado, capturas)
        assert documento.startswith(b'%PDF-')
        assert b'Ana de Prueba' in documento
        assert (b'Figura 5' in documento) is espera_grafica
        assert sum(boton.visible for boton in _botones_pdf(cliente)) == 1

    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar))


async def _ejecutar_descarga_interceptada(monkeypatch, control, capturas, al_capturar) -> list[bytes]:
    """Abre el diálogo PDF, intercepta capturas y descargas, y ejecuta generar()."""
    control.abrir()
    for clave, valor in PORTADA.items():
        control.dialogo.campos[clave].set_value(valor)
    descargas = []
    monkeypatch.setattr(ui, 'download', lambda contenido, **_ops: descargas.append(contenido))

    async def capturar_y_alterar(_identificador):
        al_capturar()
        return capturas

    monkeypatch.setattr(modulo_boton, 'capturar_regiones', capturar_y_alterar)
    monkeypatch.setattr(modulo_boton.run, 'io_bound', lambda funcion, *args: funcion(*args))
    await control.generar()
    return descargas


def test_pdf_rechaza_errores_y_edicion_durante_descarga(monkeypatch):
    """Rechaza códigos de error y cancela descargas cuando cambia la captura en vuelo."""
    for codigo in ('DIAGONAL_NULA', 'ENTRADA_INVALIDA'):
        with pytest.raises(ValueError):
            preparar_figuras('metodos_iterativos', {'estado': codigo}, [crear_captura('metodos_iterativos-resumen')])
    for codigo in ('ENTRADA_INVALIDA', 'VERIFICACION_INCONSISTENTE', 'ERROR_INTERNO'):
        with pytest.raises(ValueError):
            preparar_figuras('espacios_subespacios', {'estado': codigo}, [crear_captura('espacios_subespacios-resumen')])

    async def comprobar_iterativos(vista, _cliente):
        """Simula edición de captura mientras se capturan regiones en iterativos."""
        vista.captura.restablecer(True)
        await vista.resolver()
        control = vista.actualizar_exportacion_pdf.__self__
        descargas = await _ejecutar_descarga_interceptada(
            monkeypatch,
            control,
            [crear_captura('metodos_iterativos-resumen')],
            lambda: vista.captura.tolerancia.set_value('0.05'),
        )
        assert descargas == []
        assert control.dialogo.estado.text == textos.PDF_ERROR_OBSOLETO
        assert not control.ocupado

    async def comprobar_subespacios(vista, _cliente):
        """Simula cambio de modo mientras se capturan regiones en subespacios."""
        vista.captura.cargar_ejemplo()
        await vista.analizar()
        control = vista.actualizar_exportacion_pdf.__self__
        descargas = await _ejecutar_descarga_interceptada(
            monkeypatch,
            control,
            [crear_captura('espacios_subespacios-resumen')],
            lambda: vista.selector_modo.set_value('restricciones'),
        )
        assert descargas == []
        assert control.dialogo.estado.text == textos.PDF_ERROR_OBSOLETO
        assert not control.ocupado

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar_iterativos))
    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar_subespacios))
