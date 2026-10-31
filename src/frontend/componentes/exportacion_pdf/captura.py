"""Adaptador NiceGUI para capturar regiones sin transferir datos de la portada."""
import json

from nicegui import ui
from src.frontend import constantes as limites, textos


async def capturar_regiones(identificador: str) -> list:
    """Solicita PNG al navegador; lanza ValueError recuperable si falla la captura."""
    configuracion = {
        'maximoFiguras': limites.PDF_MAXIMO_FIGURAS,
        'maximoBytesImagen': limites.PDF_MAXIMO_BYTES_IMAGEN,
        'maximoBytesTotal': limites.PDF_MAXIMO_BYTES_TOTAL,
        'maximoLado': limites.PDF_MAXIMO_LADO,
        'maximoPixeles': limites.PDF_MAXIMO_PIXELES,
        'plazoMathjax': limites.PDF_PLAZO_MATHJAX_SEGUNDOS,
        'plazoCaptura': limites.PDF_PLAZO_CLIENTE_SEGUNDOS,
        'escala': limites.PDF_ESCALA_CAPTURA,
    }
    codigo = f'return window.scalaris.capturaPdf.capturar({json.dumps(identificador)}, {json.dumps(configuracion)});'
    try:
        respuesta = await ui.run_javascript(codigo, timeout=limites.PDF_PLAZO_CAPTURA_SEGUNDOS)
    except Exception as error:
        raise ValueError(textos.PDF_ERROR_CAPTURA) from error
    if not isinstance(respuesta, dict) or 'capturas' not in respuesta:
        raise ValueError(textos.PDF_ERROR_CAPTURA)
    return respuesta['capturas']
