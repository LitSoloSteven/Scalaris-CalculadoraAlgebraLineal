"""Disponibilidad de exportación en el piloto con controles NiceGUI reales."""
import asyncio

from nicegui import ui
from tests.comun_construccion_vistas import construir_pagina


def test_boton_pdf_se_retira_al_editar_y_recalcular(monkeypatch):
    """La acción desaparece al cambiar la huella y el siguiente cálculo crea una nueva."""
    async def comprobar(vista, cliente):
        """Resuelve, edita y limpia el sistema para comprobar el ciclo de vida del botón."""
        vista.cuadricula.cargar_datos([['1']], ['2'])
        await vista._resolver_nucleo()
        botones = [elemento for elemento in cliente.elements.values()
                   if isinstance(elemento, ui.button) and elemento.text == 'Exportar PDF']
        assert len(botones) == 1 and botones[0].visible
        assert vista.reproductor_pasos.tarjeta._props['data-pdf-captura'] == 'sistemas-procedimiento'
        vista.cuadricula.cargar_datos([['1']], ['3'])
        assert not botones[0].visible
        await vista._resolver_nucleo()
        actuales = [elemento for elemento in cliente.elements.values()
                    if isinstance(elemento, ui.button) and elemento.text == 'Exportar PDF']
        assert len(actuales) == 1 and actuales[0].visible
        vista.limpiar_todo()
        assert actuales[0].is_deleted
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))


def test_sistema_sin_solucion_exporta_y_error_no_se_ofrece(monkeypatch):
    """Un resultado sin solución es exportable; un error de entrada queda sin acción visible."""
    async def comprobar(vista, cliente):
        """Comprueba el resultado incompatible y una captura inválida en la misma vista."""
        vista.cuadricula.cargar_datos([['1'], ['1']], ['2', '3'])
        await vista._resolver_nucleo()
        assert vista.ultimo_resultado['estado'] == 'SIN_SOLUCION'
        assert any(elemento.visible for elemento in cliente.elements.values()
                   if isinstance(elemento, ui.button) and elemento.text == 'Exportar PDF')
        vista.pestanas_modo.set_value('Ecuaciones')
        vista.entradas_ecuaciones[0].set_value('x = @')
        await vista._resolver_nucleo()
        assert not any(elemento.visible for elemento in cliente.elements.values()
                       if isinstance(elemento, ui.button) and elemento.text == 'Exportar PDF')
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))
