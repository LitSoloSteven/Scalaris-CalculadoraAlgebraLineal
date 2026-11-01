"""Resultados matriciales que solo se presentan dentro del reproductor visible."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.componentes.exportacion_pdf.secuencia import preparar_secuencia
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('expresion', ['A', 'A + A', 'A + A + A'])
def test_pdf_conserva_resultado_con_cero_una_o_varias_operaciones(monkeypatch, expresion):
    """La captura tiene exactamente una matriz resultante, incluso sin tarjeta final visible."""
    async def comprobar(vista, cliente):
        """Evalúa la expresión y comprueba que el resultado numérico sea capturable."""
        vista.panel_captura_matrices.cargar_datos({'A': [['1/3']]})
        vista.entrada_expresion.set_value(expresion)
        await vista.evaluar_expresion(ui.button('Evaluar prueba'))
        control = vista.actualizar_exportacion_pdf.__self__
        with preparar_secuencia('matrices', control.enlace):
            regiones = [elemento for elemento in control.enlace.estado()[0].descendants()
                        if elemento._props.get('data-pdf-captura') == 'matrices-resultado']
            assert len(regiones) == 1
            contenido = ' '.join(elemento.content for elemento in regiones[0].descendants()
                                 if isinstance(elemento, ui.html))
            assert contenido
            assert ('frac' in contenido) if expresion != 'A + A + A' else '1' in contenido
    asyncio.run(construir_pagina(monkeypatch, 'matrices', comprobar))
