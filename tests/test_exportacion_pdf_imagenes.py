"""Entradas PNG hostiles: firma, dimensiones, cantidad, tamaño y total."""
import base64
import struct

import pytest

from src.frontend import constantes as limites
from src.frontend.controladores.exportacion_pdf.imagenes import validar_imagenes
from tests.comun_exportacion_pdf import crear_captura


def test_png_valido_se_normaliza_y_conserva_dimensiones():
    """Se obtiene un PNG verificado con su región y dimensiones originales."""
    imagen, = validar_imagenes([crear_captura()], ('sistemas-resumen',))
    assert imagen.datos.startswith(limites.PDF_FIRMA_PNG)
    assert (imagen.ancho, imagen.alto) == (160, 80)
    assert imagen.clave == 'sistemas-resumen'


@pytest.mark.parametrize('capturas', [None, [], [{}], [{'clave': 'ajena', 'png': ''}],
    [{'clave': 'sistemas-resumen', 'png': '*no-base64*'}],
    [{'clave': 'sistemas-resumen', 'png': base64.b64encode(b'GIF89a').decode()}],
    [{'clave': 'sistemas-resumen', 'png': None}], [crear_captura()] * 2])
def test_rechaza_estructura_firma_y_regiones_duplicadas(capturas):
    """Ninguna entrada ajena o malformada llega a convertirse en figura."""
    with pytest.raises(ValueError, match='capturas'):
        validar_imagenes(capturas, ('sistemas-resumen',))


def test_rechaza_cantidad_y_presupuesto_antes_de_abrir_imagenes(monkeypatch):
    """Los presupuestos se verifican antes de descomprimir cualquier PNG."""
    captura = crear_captura()
    with pytest.raises(ValueError):
        validar_imagenes([captura] * (limites.PDF_MAXIMO_FIGURAS + 1), ('sistemas-resumen',))
    monkeypatch.setattr(limites, 'PDF_MAXIMO_BYTES_IMAGEN', 10)
    with pytest.raises(ValueError):
        validar_imagenes([captura], ('sistemas-resumen',))


def test_rechaza_total_y_png_truncado(monkeypatch):
    """El límite total y la integridad real del archivo se comprueban por separado."""
    captura = crear_captura()
    monkeypatch.setattr(limites, 'PDF_MAXIMO_BYTES_TOTAL', 10)
    with pytest.raises(ValueError):
        validar_imagenes([captura], ('sistemas-resumen',))
    monkeypatch.setattr(limites, 'PDF_MAXIMO_BYTES_TOTAL', 1_000_000)
    captura['png'] = base64.b64encode(base64.b64decode(captura['png'])[:40]).decode()
    with pytest.raises(ValueError):
        validar_imagenes([captura], ('sistemas-resumen',))


@pytest.mark.parametrize('dimensiones', [(0, 1), (4097, 1), (4096, 4096), (1, 2**31)])
def test_dimension_falsa_se_rechaza_antes_de_pillow(monkeypatch, dimensiones):
    """Una cabecera manipulada no puede forzar una reserva masiva de píxeles."""
    from src.frontend.controladores.exportacion_pdf import imagenes
    captura = crear_captura()
    datos = bytearray(base64.b64decode(captura['png']))
    datos[16:24] = struct.pack('>II', *dimensiones)
    captura['png'] = base64.b64encode(datos).decode()
    def no_abrir(*argumentos, **opciones):
        """Falla si se intenta abrir una cabecera con dimensiones prohibidas."""
        pytest.fail('No se debe abrir una imagen con dimensiones excesivas')
    monkeypatch.setattr(imagenes.Image, 'open', no_abrir)
    with pytest.raises(ValueError):
        validar_imagenes([captura], ('sistemas-resumen',))
