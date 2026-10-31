"""Exportación de cálculos reales y retiro de copias en las vistas algebraicas."""
import asyncio

import pytest
from nicegui import ui
from src.frontend import textos
from src.frontend.controladores.exportacion_pdf.documento import generar_pdf
from tests.comun_exportacion_pdf import PORTADA, crear_captura
from tests.comun_exportacion_algebra import (
    HERRAMIENTAS, construir_algebra, calcular_algebra, editar_algebra, regiones_control,
)


@pytest.mark.parametrize('herramienta', HERRAMIENTAS)
def test_calculo_real_exportable_sin_copia_y_edicion_lo_retira(monkeypatch, herramienta):
    """Cada herramienta ofrece un único PDF vigente y regiones independientes registradas."""
    async def comprobar(vista, cliente):
        """Verifica marcado, documento real e invalidación desde la captura montada."""
        await calcular_algebra(herramienta, vista)
        control = vista.actualizar_exportacion_pdf.__self__
        botones = [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.button)]
        assert sum(boton.text == textos.PDF_EXPORTAR and boton.visible for boton in botones) == 1
        assert not any(boton.text in ('Copiar resultado', 'Copiar A⁻¹') for boton in botones)
        assert control.enlace.vigente(control.resultado)
        assert control.enlace.raiz == f'c{control.enlace.estado()[0].id}'
        regiones = regiones_control(control)
        claves = [region._props['data-pdf-captura'] for region in regiones]
        assert len(claves) == len(set(claves))
        assert f'{control.herramienta}-resumen' in claves
        assert set(claves) <= textos.PDF_REGIONES_ALGEBRA[control.herramienta].keys()
        assert not any('data-pdf-captura' in ancestro._props for region in regiones for ancestro in region.ancestors())
        documento, _ = generar_pdf(control.herramienta, PORTADA, control.resultado,
                                   [crear_captura(clave) for clave in claves])
        assert documento.startswith(b'%PDF-')
        assert b'Ana de Prueba' in documento and b'Figura 1' in documento
        testigo = control.enlace.testigo()
        editar_algebra(herramienta, vista)
        assert control.boton.is_deleted or not control.boton.visible
        assert not control.enlace.comprobar(testigo, control.resultado)
    asyncio.run(construir_algebra(monkeypatch, herramienta, comprobar))
