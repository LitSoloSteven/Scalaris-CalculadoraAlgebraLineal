"""Carreras de exportación y privacidad de la portada con controles reales."""
import asyncio

import pytest
from nicegui import ui
from src.frontend.componentes.exportacion_pdf import boton as modulo_boton
from src.frontend.componentes.exportacion_pdf.boton import ExportacionPDF
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_exportacion_pdf import PORTADA, crear_captura


def _crear_trabajador(vista, control, cambio):
    async def trabajar(funcion, *argumentos):
        """Aplica una modificación concurrente antes de completar el generador real."""
        if cambio == 'editar': vista.cuadricula.cargar_datos([['1']], ['3'])
        if cambio == 'revision': vista._revision_captura += 1
        if cambio == 'limpiar': vista.limpiar_todo()
        if cambio == 'cerrar': control.dialogo.dialogo.close()
        if cambio == 'fallar': raise RuntimeError('detalle interno confidencial')
        return funcion(*argumentos)
    return trabajar


@pytest.mark.parametrize('cambio', ['ninguno', 'editar', 'revision', 'limpiar', 'cerrar', 'fallar'])
def test_descarga_solo_si_sigue_vigente_y_dialogo_abierto(monkeypatch, cambio):
    """Una edición, cancelación o limpieza mientras trabaja impide entregar el archivo."""
    async def comprobar(vista, cliente):
        """Genera con transporte simulado y comprueba que una carrera impide descargar."""
        vista.cuadricula.cargar_datos([['1']], ['2'])
        await vista._resolver_nucleo()
        control = vista.actualizar_exportacion_pdf.__self__
        assert isinstance(control, ExportacionPDF)
        temporizador = vista.reproductor_pasos.temporizador
        control.abrir()
        for clave, valor in PORTADA.items():
            control.dialogo.campos[clave].set_value(valor)
        descargas = []
        monkeypatch.setattr(ui, 'download', lambda *argumentos, **opciones: descargas.append(opciones))
        async def capturar(identificador):
            """Entrega una imagen sintética sin depender del navegador."""
            return [crear_captura()]
        monkeypatch.setattr(modulo_boton, 'capturar_regiones', capturar)
        monkeypatch.setattr(modulo_boton.run, 'io_bound', _crear_trabajador(vista, control, cambio))
        await control.generar()
        assert len(descargas) == int(cambio == 'ninguno')
        assert not control.ocupado
        if cambio == 'ninguno':
            assert vista.reproductor_pasos.temporizador is temporizador
            vista.reproductor_pasos._alternar_reproduccion()
            assert vista.reproductor_pasos.temporizador.active
        if cambio == 'fallar':
            assert 'detalle interno' not in control.dialogo.estado.text
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))


def test_cerrar_borra_campos_y_validar_muestra_errores_por_campo(monkeypatch):
    """El diálogo se reutiliza sin retener datos al cerrar y señala cada campo inválido."""
    async def comprobar(vista, cliente):
        """Verifica errores visibles y el restablecimiento de los campos al cerrar."""
        vista.cuadricula.cargar_datos([['1']], ['2'])
        await vista._resolver_nucleo()
        control = vista.actualizar_exportacion_pdf.__self__
        control.abrir()
        assert control.dialogo.validar() is None
        assert all(error.text for error in control.dialogo.errores.values())
        for clave, valor in PORTADA.items():
            control.dialogo.campos[clave].set_value(valor)
        control.dialogo._al_cerrar()
        assert all(campo.value == '' for campo in control.dialogo.campos.values())
        assert all(campo._props['aria-invalid'] == 'false' for campo in control.dialogo.campos.values())
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))
