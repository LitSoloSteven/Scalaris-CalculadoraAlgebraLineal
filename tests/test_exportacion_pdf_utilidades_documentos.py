"""Regiones obligatorias, documento y límites de las utilidades numéricas y gráficas."""
import re

import pytest
from src.frontend import textos
from src.frontend.controladores.exportacion_pdf.documento import generar_pdf
from src.frontend.controladores.exportacion_pdf.figuras import preparar_figuras
from tests.comun_exportacion_pdf import PORTADA, crear_captura


@pytest.mark.parametrize('herramienta', textos.PDF_REGIONES_UTILIDADES)
def test_documento_incluye_portada_y_figuras_registradas(herramienta):
    """Cada utilidad genera todas sus figuras consecutivas y sus notas en español."""
    registro = textos.PDF_REGIONES_UTILIDADES[herramienta]
    capturas = [crear_captura(clave) for clave in registro]
    figuras = preparar_figuras(herramienta, {'estado': 'EXITO'}, capturas)
    assert [figura['titulo'] for figura in figuras] == [datos[0] for datos in registro.values()]
    documento, _ = generar_pdf(herramienta, PORTADA, {'estado': 'EXITO'}, capturas)
    assert documento.startswith(b'%PDF-')
    assert len(re.findall(rb'/Type\s*/Page\b', documento)) >= 2
    assert b'Ana de Prueba' in documento and b'Docente de Prueba' in documento
    assert b'Grupo A12' in documento and b'15 de octubre de 2026' in documento
    assert b'Figura 1' in documento and b'Figura 2' in documento


@pytest.mark.parametrize('herramienta', textos.PDF_REGIONES_UTILIDADES)
def test_utilidad_rechaza_regiones_incompletas_ajenas_y_estado_error(herramienta):
    """No se puede producir un PDF con solo pasos, imagen ajena o resultado fallido."""
    claves = textos.PDF_REGIONES_OBLIGATORIAS[herramienta]
    completas = [crear_captura(clave) for clave in claves]
    invalidas = [[crear_captura()], [*completas, completas[0]], []]
    invalidas.extend([[crear_captura(clave)] for clave in claves] if len(claves) > 1
                     else [[crear_captura(f'{herramienta}-procedimiento')]])
    for capturas in invalidas:
        with pytest.raises(ValueError):
            preparar_figuras(herramienta, {'estado': 'EXITO'}, capturas)
    with pytest.raises(ValueError):
        preparar_figuras(herramienta, {'estado': 'ERROR'}, completas)
