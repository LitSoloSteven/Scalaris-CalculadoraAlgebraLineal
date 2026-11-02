"""Generación en memoria de documentos estudiantiles APA con figuras reales."""
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Spacer
from src.frontend import constantes as medidas, textos
from .estilos import crear_estilos, parrafo
from .figuras import construir_figura, preparar_figuras
from .portada import fecha_espanola, validar_portada


def generar_pdf(herramienta: str, datos_portada: dict, resultado: dict, capturas: list) -> tuple[bytes, bool]:
    """Genera PDF y aviso de reducción sin archivos; lanza ValueError por entrada inválida."""
    portada, errores = validar_portada(datos_portada)
    if errores or herramienta not in textos.PDF_HERRAMIENTAS:
        raise ValueError(textos.PDF_ERROR_GENERACION)
    figuras = preparar_figuras(herramienta, resultado, capturas)
    salida = BytesIO()
    documento = _crear_documento(salida)
    estilos = crear_estilos()
    titulo = textos.PDF_TITULO_RESULTADO.format(herramienta=textos.PDF_HERRAMIENTAS[herramienta])
    bloques = _portada(portada, titulo, estilos)
    bloques.extend([PageBreak(), parrafo(titulo, estilos['nivel1']), parrafo(textos.PDF_SECCION, estilos['nivel1'])])
    reducida = False
    espacio = (documento.width, documento.height)
    for numero, figura in enumerate(figuras, start=1):
        bloque, aviso = construir_figura(figura, numero, estilos, espacio)
        bloques.append(bloque)
        reducida = reducida or aviso
    documento.build(bloques)
    return salida.getvalue(), reducida


def _crear_documento(salida: BytesIO) -> BaseDocTemplate:
    documento = BaseDocTemplate(salida, pagesize=letter, leftMargin=medidas.PDF_MARGEN_PUNTOS,
                               rightMargin=medidas.PDF_MARGEN_PUNTOS, topMargin=medidas.PDF_MARGEN_PUNTOS,
                               bottomMargin=medidas.PDF_MARGEN_PUNTOS + medidas.PDF_DESPLAZAMIENTO_PAGINA,
                               pageCompression=0, title=textos.PDF_MARCA, author='', creator=textos.PDF_MARCA)
    marco = Frame(documento.leftMargin, documento.bottomMargin, documento.width, documento.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    documento.addPageTemplates(PageTemplate(id='apa', frames=[marco], onPage=_decorar_pagina))
    return documento


def _portada(portada: dict, titulo: str, estilos: dict) -> list:
    bloques = [Spacer(1, medidas.PDF_LINEAS_PORTADA * medidas.PDF_INTERLINEADO_PUNTOS),
               parrafo(titulo, estilos['nivel1']), Spacer(1, medidas.PDF_INTERLINEADO_PUNTOS)]
    lineas = (portada['nombre'], textos.PDF_AFILIACION, textos.PDF_GRUPO.format(grupo=portada['grupo']),
              textos.PDF_DOCENTE.format(docente=portada['docente']), fecha_espanola(portada['fecha']))
    bloques.extend(parrafo(linea, estilos['centrado']) for linea in lineas)
    return bloques


def _decorar_pagina(lienzo, documento) -> None:
    ancho, alto = letter
    lienzo.saveState()
    lienzo.setFont('Times-Roman', medidas.PDF_TEXTO_PUNTOS)
    lienzo.drawRightString(ancho - medidas.PDF_MARGEN_PUNTOS,
                          alto - medidas.PDF_MARGEN_PUNTOS + medidas.PDF_DESPLAZAMIENTO_PAGINA,
                          str(documento.page))
    lienzo.setFont('Times-Italic', medidas.PDF_MARCA_PUNTOS)
    lienzo.setFillColor(HexColor(medidas.PDF_GRIS_MARCA))
    lienzo.drawRightString(ancho - medidas.PDF_MARGEN_PUNTOS, medidas.PDF_MARGEN_PUNTOS, textos.PDF_MARCA)
    lienzo.restoreState()
