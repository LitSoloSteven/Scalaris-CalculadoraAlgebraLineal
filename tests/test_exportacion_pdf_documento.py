"""Estructura PDF, portada APA, figuras, escape y geometría del documento."""
import re
from io import BytesIO

import pytest
from reportlab.lib.pagesizes import letter
from src.frontend import constantes as medidas, textos
from src.frontend.controladores.exportacion_pdf.documento import generar_pdf, _crear_documento
from src.frontend.controladores.exportacion_pdf.estilos import crear_estilos, parrafo
from src.frontend.controladores.exportacion_pdf.figuras import preparar_figuras
from tests.comun_exportacion_pdf import PORTADA, RESULTADO, crear_captura


def test_pdf_valido_con_dos_paginas_y_cuatro_datos():
    """El caso mínimo produce portada y página de resultado con una imagen y nota."""
    documento, reducida = generar_pdf('sistemas', PORTADA, RESULTADO, [crear_captura()])
    assert documento.startswith(b'%PDF-')
    assert len(re.findall(rb'/Type\s*/Page\b', documento)) == 2
    for texto in ('Ana de Prueba', 'Docente de Prueba', 'Grupo A12', '15 de octubre de 2026', 'UAM'):
        assert texto.encode('ascii') in documento
    assert b'/Subtype /Image' in documento and b'Figura 1' in documento and b'(Nota.)' in documento
    assert b'/MediaBox [ 0 0 612 792 ]' in documento
    assert documento.count(b'(Scalaris) Tj') == 2
    assert b'/BaseFont /Times-Italic' in documento
    assert not reducida


def test_escapa_metacaracteres_y_no_interpreta_portada_como_marcado():
    """El texto plano del párrafo conserva literalmente etiquetas falsas y ampersand."""
    texto = '<b>Ana & Sol</b> > <img src="ruta">'
    bloque = parrafo(texto, crear_estilos()['cuerpo'])
    assert '&lt;b&gt;' in bloque.text and '&amp;' in bloque.text
    assert bloque.getPlainText() == texto
    assert all(fragmento.fontName == 'Times-Roman' for fragmento in bloque.frags)
    documento, _ = generar_pdf('sistemas', {**PORTADA, 'nombre': texto}, RESULTADO, [crear_captura()])
    assert documento.startswith(b'%PDF-')


def test_figuras_altas_se_reducen_con_aviso_y_numeracion_consecutiva():
    """Dos figuras altas caben sin deformar ni fallos de maquetación y explican su reducción."""
    capturas = [crear_captura(dimensiones=(200, 3000)),
                crear_captura('sistemas-procedimiento', (200, 3000))]
    documento, reducida = generar_pdf('sistemas', PORTADA, RESULTADO, capturas)
    assert reducida and b'Figura 1' in documento and b'Figura 2' in documento
    assert len(re.findall(rb'/Type\s*/Page\b', documento)) == 3
    assert documento.count(b'(Scalaris) Tj') == 3


def test_estilos_apa_sangria_doble_espacio_y_alineacion():
    """Las medidas declaradas mantienen carta, Times 12, doble espacio y sangría de 36 puntos."""
    estilos = crear_estilos()
    assert letter == (612, 792) and medidas.PDF_MARGEN_PUNTOS == 72
    assert estilos['cuerpo'].fontName == 'Times-Roman'
    assert estilos['cuerpo'].fontSize == 12 and estilos['cuerpo'].leading == 24
    assert estilos['cuerpo'].firstLineIndent == 36
    assert estilos['nivel1'].alignment == 1 and estilos['nivel2'].alignment == 0


def test_rechaza_glifos_desconocidos_y_regiones_no_registradas():
    """Nunca deja que Times sustituya un símbolo ausente ni admite una captura ajena."""
    with pytest.raises(ValueError, match='caracteres'):
        parrafo('A⁻¹', crear_estilos()['cuerpo'])
    with pytest.raises(ValueError):
        preparar_figuras('sistemas', RESULTADO, [crear_captura('inversa')])
    with pytest.raises(ValueError):
        generar_pdf('sistemas', PORTADA, {'estado': 'ERROR'}, [crear_captura()])
    assert textos.PDF_AFILIACION == 'UAM'


def test_portada_con_nombres_maximos_envuelve_sin_agregar_paginas():
    """Los límites de nombre y docente caben en portada aunque sean palabras continuas."""
    portada = {**PORTADA, 'nombre': 'W' * medidas.PDF_MAXIMO_NOMBRE,
               'docente': 'W' * medidas.PDF_MAXIMO_DOCENTE}
    documento, _ = generar_pdf('sistemas', portada, RESULTADO, [crear_captura()])
    assert len(re.findall(rb'/Type\s*/Page\b', documento)) == 2


def test_marco_sin_relleno_implicito_y_pie_reservado():
    """El cuerpo inicia exactamente a una pulgada y conserva un pie libre para Scalaris."""
    documento = _crear_documento(BytesIO())
    marco = documento.pageTemplates[0].frames[0]
    assert marco._x1 == 72 and marco._y2 == 720
    assert marco._leftPadding == marco._rightPadding == marco._topPadding == 0
    assert marco._y1 == 96
