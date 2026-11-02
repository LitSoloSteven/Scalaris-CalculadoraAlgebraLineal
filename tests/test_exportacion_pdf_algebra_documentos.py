"""Catálogo de documentos algebraicos y rechazo de capturas ajenas o incompletas."""
import re

import pytest
from src.frontend import textos
from src.frontend.controladores.exportacion_pdf.documento import generar_pdf
from src.frontend.controladores.exportacion_pdf.figuras import preparar_figuras
from tests.comun_exportacion_pdf import PORTADA, crear_captura

CASOS = [(herramienta, estado) for herramienta, estados in textos.PDF_ESTADOS_POR_HERRAMIENTA.items()
         if herramienta != 'sistemas' for estado in estados]


@pytest.mark.parametrize('herramienta,estado', CASOS)
def test_cada_estado_admitido_genera_portada_y_resultado(herramienta, estado):
    """Los estados no erróneos generan un documento válido con descripción española."""
    claves = textos.PDF_REGIONES_OBLIGATORIAS.get(herramienta, (f'{herramienta}-resumen',))
    capturas = [crear_captura(clave) for clave in claves]
    resultado = {'estado': estado}
    figuras = preparar_figuras(herramienta, resultado, capturas)
    descripcion = textos.PDF_ESTADOS_POR_HERRAMIENTA[herramienta][estado]
    assert descripcion in figuras[0]['descripcion']
    documento, reducida = generar_pdf(herramienta, PORTADA, resultado, capturas)
    assert documento.startswith(b'%PDF-') and not reducida
    assert len(re.findall(rb'/Type\s*/Page\b', documento)) == 2
    assert b'Grupo A12' in documento and b'Docente de Prueba' in documento
    assert b'15 de octubre de 2026' in documento and b'(Nota.)' in documento


@pytest.mark.parametrize('herramienta', textos.PDF_REGIONES_ALGEBRA)
def test_regiones_ajenas_duplicadas_y_errores_se_rechazan(herramienta):
    """El registro impide mezclar herramientas, omitir el resumen o exportar errores."""
    resumen = crear_captura(f'{herramienta}-resumen')
    procedimiento = crear_captura(f'{herramienta}-procedimiento')
    resultado = {'estado': 'EXITO'}
    for capturas in ([crear_captura()], [procedimiento], [resumen, resumen]):
        with pytest.raises(ValueError):
            preparar_figuras(herramienta, resultado, capturas)
    with pytest.raises(ValueError):
        preparar_figuras(herramienta, {'estado': 'ERROR'}, [resumen])
    with pytest.raises(ValueError):
        preparar_figuras(herramienta, {'estado': 'DESCONOCIDO'}, [resumen])
