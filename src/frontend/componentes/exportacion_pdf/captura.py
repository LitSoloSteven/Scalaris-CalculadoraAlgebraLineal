"""Transporte acotado de capturas PNG sin exceder el tamaño de mensajes de NiceGUI."""
import json

from nicegui import ui
from src.frontend import constantes as limites, textos


async def capturar_regiones(identificador: str) -> list:
    """Solicita y recupera PNG en fragmentos; libera el cliente incluso ante errores."""
    respuesta = await _ejecutar('preparar', identificador, _configuracion())
    solicitud = respuesta.get('solicitud') if isinstance(respuesta, dict) else None
    if type(solicitud) is not int or solicitud < 1:
        raise ValueError(textos.PDF_ERROR_CAPTURA)
    try:
        manifiesto = _validar_manifiesto(respuesta)
        return [await _recuperar(solicitud, indice, figura) for indice, figura in enumerate(manifiesto)]
    finally:
        try:
            await _ejecutar('liberar', solicitud)
        except ValueError:
            pass


def _configuracion() -> dict:
    return {
        'maximoFiguras': limites.PDF_MAXIMO_FIGURAS,
        'maximoBytesImagen': limites.PDF_MAXIMO_BYTES_IMAGEN,
        'maximoBytesTotal': limites.PDF_MAXIMO_BYTES_TOTAL,
        'maximoLado': limites.PDF_MAXIMO_LADO,
        'maximoPixeles': limites.PDF_MAXIMO_PIXELES,
        'plazoMathjax': limites.PDF_PLAZO_MATHJAX_SEGUNDOS,
        'plazoCaptura': limites.PDF_PLAZO_CLIENTE_SEGUNDOS,
        'escala': limites.PDF_ESCALA_CAPTURA,
    }


async def _ejecutar(funcion: str, *argumentos):
    parametros = ', '.join(json.dumps(argumento) for argumento in argumentos)
    codigo = f'return window.scalaris.capturaPdf.{funcion}({parametros});'
    try:
        return await ui.run_javascript(codigo, timeout=limites.PDF_PLAZO_CAPTURA_SEGUNDOS)
    except Exception as error:
        raise ValueError(textos.PDF_ERROR_CAPTURA) from error


def _validar_manifiesto(respuesta: dict) -> list:
    figuras = respuesta.get('capturas')
    if not isinstance(figuras, list) or not 0 < len(figuras) <= limites.PDF_MAXIMO_FIGURAS:
        raise ValueError(textos.PDF_ERROR_CAPTURA)
    total = sum(_longitud_figura(figura) for figura in figuras)
    if total > ((limites.PDF_MAXIMO_BYTES_TOTAL + 2) // 3) * 4:
        raise ValueError(textos.PDF_ERROR_CAPTURA)
    return figuras


def _longitud_figura(figura: dict) -> int:
    maximo = ((limites.PDF_MAXIMO_BYTES_IMAGEN + 2) // 3) * 4
    if (not isinstance(figura, dict) or not isinstance(figura.get('clave'), str)
            or type(figura.get('longitud')) is not int or not 0 < figura['longitud'] <= maximo):
        raise ValueError(textos.PDF_ERROR_CAPTURA)
    return figura['longitud']


async def _recuperar(solicitud: int, indice: int, figura: dict) -> dict:
    fragmentos = []
    for desplazamiento in range(0, figura['longitud'], limites.PDF_FRAGMENTO_CARACTERES):
        cantidad = min(limites.PDF_FRAGMENTO_CARACTERES, figura['longitud'] - desplazamiento)
        fragmento = await _ejecutar('leer', solicitud, indice, desplazamiento, cantidad)
        if not isinstance(fragmento, str) or len(fragmento) != cantidad:
            raise ValueError(textos.PDF_ERROR_CAPTURA)
        fragmentos.append(fragmento)
    return {'clave': figura['clave'], 'png': ''.join(fragmentos)}
