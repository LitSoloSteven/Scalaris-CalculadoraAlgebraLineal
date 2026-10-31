"""Cobertura de caracteres de las fuentes base utilizadas en el documento."""
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase._glyphlist import _glyphname2unicode


def texto_admitido(texto: str) -> bool:
    """Indica si Times puede representar cada carácter sin fuentes de sustitución."""
    fuente = pdfmetrics.getFont('Times-Roman')
    caracteres = {chr(_glyphname2unicode[nombre]) for nombre in fuente.encoding.vector
                  if nombre in _glyphname2unicode}
    return all(caracter in caracteres and caracter.isprintable() for caracter in texto)
