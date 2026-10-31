"""Datos sintéticos y PNG mínimos para probar exportación sin datos personales reales."""
import base64
from io import BytesIO

from PIL import Image

PORTADA = {'nombre': 'Ana de Prueba', 'docente': 'Docente de Prueba', 'grupo': 'A12', 'fecha': '2026-10-15'}
RESULTADO = {'estado': 'SOLUCION_UNICA', 'solucion': ['2']}


def crear_captura(clave='sistemas-resumen', dimensiones=(160, 80)) -> dict:
    """Devuelve un PNG sintético blanco del tamaño solicitado con su clave de región."""
    salida = BytesIO()
    with Image.new('RGB', dimensiones, 'white') as imagen:
        imagen.save(salida, format='PNG')
    return {'clave': clave, 'png': base64.b64encode(salida.getvalue()).decode('ascii')}
