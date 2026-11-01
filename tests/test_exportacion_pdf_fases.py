"""Estados de captura, indicadores temporales y contenido estático de comprobaciones."""
import asyncio

from nicegui import ui

from src.frontend import textos
from src.frontend.componentes.exportacion_pdf import boton as modulo_boton
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_exportacion_algebra import calcular_algebra
from tests.comun_exportacion_pdf import PORTADA, crear_captura


def _verificar_indicadores(control, ocupado):
    """Comprueba visibilidad y retirada de la capa sin depender de animaciones del navegador."""
    indicadores = (control.indicador, control.dialogo.indicador, control.dialogo.indicador_confirmar)
    for indicador in indicadores:
        assert indicador.visible is ocupado
        assert ('data-destacada-activa' in indicador._props) is ocupado
        assert indicador._props['role'] == 'status'
    assert not control.boton._props.get('loading')
    assert not control.dialogo.confirmar._props.get('loading')


def test_generacion_anuncia_captura_y_documento_y_retira_indicadores(monkeypatch):
    """Cada tarea observa su texto de fase y los indicadores se retiran tras descargar."""
    async def comprobar(vista, cliente):
        """Aísla transporte y trabajador conservando los controles y estados reales."""
        vista.cuadricula.cargar_datos([['1']], ['2'])
        await vista._resolver_nucleo()
        control = vista.actualizar_exportacion_pdf.__self__
        control.abrir()
        for clave, valor in PORTADA.items():
            control.dialogo.campos[clave].set_value(valor)
        _verificar_indicadores(control, False)
        async def capturar(identificador):
            """Observa la fase de captura antes de devolver su imagen sintética."""
            assert control.dialogo.estado.text == textos.PDF_CAPTURANDO == 'Capturando el resultado…'
            _verificar_indicadores(control, True)
            return [crear_captura()]
        async def trabajar(funcion, *argumentos):
            """Observa la fase del documento antes de generar con ReportLab."""
            assert control.dialogo.estado.text == textos.PDF_GENERANDO == 'Generando el documento…'
            return funcion(*argumentos)
        descargas = []
        monkeypatch.setattr(modulo_boton, 'capturar_regiones', capturar)
        monkeypatch.setattr(modulo_boton.run, 'io_bound', trabajar)
        monkeypatch.setattr(ui, 'download', lambda *argumentos, **opciones: descargas.append(argumentos))
        await control.generar()
        assert len(descargas) == 1
        _verificar_indicadores(control, False)
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))


def test_error_de_captura_retira_las_capas_y_conserva_un_mensaje(monkeypatch):
    """El estado de error permite reintentar sin dejar animaciones activas."""
    async def comprobar(vista, cliente):
        """Fuerza un error del transporte con el diálogo real abierto."""
        vista.cuadricula.cargar_datos([['1']], ['2'])
        await vista._resolver_nucleo()
        control = vista.actualizar_exportacion_pdf.__self__
        control.abrir()
        for clave, valor in PORTADA.items():
            control.dialogo.campos[clave].set_value(valor)
        async def fallar(identificador):
            """Emula un transporte fallido sin enviar detalles internos."""
            raise ValueError('captura simulada')
        monkeypatch.setattr(modulo_boton, 'capturar_regiones', fallar)
        await control.generar()
        assert control.dialogo.estado.text == textos.PDF_ERROR_CAPTURA
        _verificar_indicadores(control, False)
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))


def _verificar_resumen_comprobaciones(elementos, comprobaciones):
    """Comprueba títulos recibidos, distintivos y fórmulas del contenido estático."""
    titulos = {elemento.text for elemento in elementos if isinstance(elemento, ui.label)}
    for comprobacion in comprobaciones:
        assert comprobacion['titulo'] in titulos
    assert any(isinstance(elemento, ui.badge) and elemento.text == 'Correcto' for elemento in elementos)
    assert any(isinstance(elemento, ui.html) and '$$' in elemento.content for elemento in elementos)


def _verificar_detalles_excluidos(elementos):
    """Exige que cada control diferido esté cerrado y excluido del documento estático."""
    detalles = [elemento for elemento in elementos if isinstance(elemento, ui.expansion)]
    assert detalles
    assert all('data-pdf-excluir' in detalle._props and detalle.value is False for detalle in detalles)


def test_comprobaciones_inicialmente_abiertas_y_detalles_excluidos(monkeypatch):
    """El árbol conserva títulos, distintivos y fórmulas sin montar detalles diferidos."""
    async def comprobar(vista, cliente):
        """Inspecciona las comprobaciones reales de una inversa calculada."""
        await calcular_algebra('inversa', vista)
        control = vista.actualizar_exportacion_pdf.__self__
        region = next(elemento for elemento in cliente.elements.values()
                      if elemento._props.get('data-pdf-captura') == 'inversa-comprobaciones')
        assert region.value is True
        assert 'default-opened' not in region._props
        elementos = list(region.descendants())
        _verificar_resumen_comprobaciones(elementos, control.resultado['comprobaciones'])
        _verificar_detalles_excluidos(elementos)
    asyncio.run(construir_pagina(monkeypatch, 'inversa', comprobar))
