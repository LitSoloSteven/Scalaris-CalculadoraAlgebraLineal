"""Estilos tipográficos y escape centralizado para párrafos APA."""
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from src.frontend import constantes as medidas, textos
from .glifos import texto_admitido


def crear_estilos() -> dict[str, ParagraphStyle]:
    """Construye estilos Times 12 con doble espacio y encabezados APA de dos niveles."""
    cuerpo = ParagraphStyle('cuerpo', fontName='Times-Roman', fontSize=medidas.PDF_TEXTO_PUNTOS,
                            leading=medidas.PDF_INTERLINEADO_PUNTOS, alignment=TA_LEFT,
                            firstLineIndent=medidas.PDF_SANGRIA_PUNTOS, splitLongWords=True)
    return {
        'cuerpo': cuerpo,
        'centrado': ParagraphStyle('centrado', parent=cuerpo, alignment=TA_CENTER, firstLineIndent=0),
        'nivel1': ParagraphStyle('nivel1', parent=cuerpo, fontName='Times-Bold',
                                 alignment=TA_CENTER, firstLineIndent=0),
        'nivel2': ParagraphStyle('nivel2', parent=cuerpo, fontName='Times-Bold', firstLineIndent=0),
        'figura': ParagraphStyle('figura', parent=cuerpo, firstLineIndent=0),
        'cursiva': ParagraphStyle('cursiva', parent=cuerpo, fontName='Times-Italic', firstLineIndent=0),
    }


def parrafo(texto: str, estilo: ParagraphStyle, nota: bool = False) -> Paragraph:
    """Escapa texto literal; ante glifos ausentes lanza ValueError sin exponer el texto."""
    if not texto_admitido(texto):
        raise ValueError(textos.PDF_ERROR_GLIFOS)
    contenido = escape(texto)
    if nota:
        contenido = f'<i>{escape(textos.PDF_NOTA)}</i> {contenido}'
    return Paragraph(contenido, estilo)
