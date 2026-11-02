"""Validación acotada de PNG recibidos del cliente antes de descomprimirlos."""
import base64
import binascii
import struct
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from src.frontend import constantes as limites, textos


@dataclass(frozen=True)
class ImagenValidada:
    """PNG sin metadatos, dimensiones verificadas y clave de región conocida."""
    clave: str
    datos: bytes
    ancho: int
    alto: int


def validar_imagenes(capturas: list, claves: tuple[str, ...]) -> tuple[ImagenValidada, ...]:
    """Valida cantidad, claves y presupuestos antes de abrir PNG; lanza ValueError seguro."""
    if not isinstance(capturas, list) or not 0 < len(capturas) <= limites.PDF_MAXIMO_FIGURAS:
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    vistas, total = set(), 0
    for captura in capturas:
        if not isinstance(captura, dict) or captura.get('clave') not in claves:
            raise ValueError(textos.PDF_ERROR_IMAGEN)
        clave = captura['clave']
        contenido = captura.get('png')
        if clave in vistas or not isinstance(contenido, str):
            raise ValueError(textos.PDF_ERROR_IMAGEN)
        vistas.add(clave)
        total += _presupuesto_base64(contenido)
    if total > limites.PDF_MAXIMO_BYTES_TOTAL:
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    return tuple(_validar_png(captura) for captura in capturas)


def _presupuesto_base64(contenido: str) -> int:
    maximo_codificado = ((limites.PDF_MAXIMO_BYTES_IMAGEN + 2) // 3) * 4
    if not contenido or len(contenido) > maximo_codificado:
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    return (len(contenido) // 4) * 3 - len(contenido) + len(contenido.rstrip('='))


def _cabecera_png(datos: bytes) -> tuple[int, int]:
    if len(datos) < 33 or not datos.startswith(limites.PDF_FIRMA_PNG):
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    longitud, tipo, ancho, alto = struct.unpack('>I4sII', datos[8:24])
    if longitud != 13 or tipo != b'IHDR':
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    if not 0 < ancho <= limites.PDF_MAXIMO_LADO or not 0 < alto <= limites.PDF_MAXIMO_LADO:
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    if ancho * alto > limites.PDF_MAXIMO_PIXELES:
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    return ancho, alto


def _validar_png(captura: dict) -> ImagenValidada:
    try:
        datos = base64.b64decode(captura['png'], validate=True)
        if len(datos) > limites.PDF_MAXIMO_BYTES_IMAGEN:
            raise ValueError
        ancho, alto = _cabecera_png(datos)
        with Image.open(BytesIO(datos), formats=('PNG',)) as imagen:
            imagen.verify()
        with Image.open(BytesIO(datos), formats=('PNG',)) as imagen:
            if imagen.size != (ancho, alto) or getattr(imagen, 'n_frames', 1) != 1:
                raise ValueError
            imagen.load()
            limpia = BytesIO()
            imagen.convert('RGB').save(limpia, format='PNG')
        return ImagenValidada(captura['clave'], limpia.getvalue(), ancho, alto)
    except (ValueError, TypeError, binascii.Error, OSError, UnidentifiedImageError,
            Image.DecompressionBombError, SyntaxError) as error:
        raise ValueError(textos.PDF_ERROR_IMAGEN) from error
