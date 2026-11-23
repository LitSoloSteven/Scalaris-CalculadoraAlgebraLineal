"""Despacho de Jacobi y adaptación de su respuesta exacta para la interfaz."""
from dataclasses import asdict
from fractions import Fraction

from src.backend.resolutores.sistemas_lineales.iterativos.formato_iterativo import formatear_racional_exacto
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import resolver_jacobi_desde_captura
from ..nucleo.captura_iterativa import SistemaCapturado, interpretar_ecuaciones


_EJEMPLO = '8*x1 - x2 + x3 = 5\n2*x1 + 10*x2 - x3 = 23\nx1 - x2 + 6*x3 = -7'
TOLERANCIA_INICIAL = '0.001'
MAXIMO_INICIAL = '25'


def ejemplo_iterativo() -> SistemaCapturado:
    """Devuelve el ejemplo de tres incógnitas listo para cargar en cualquiera de los modos."""
    return interpretar_ecuaciones(_EJEMPLO)


def resolver_iterativo(captura: dict) -> dict:
    """Calcula Jacobi desde una instantánea de la vista y devuelve datos serializables."""
    try:
        sistema = _obtener_sistema(captura)
    except ValueError as error:
        return {
            'codigo': 'ENTRADA_INVALIDA', 'pasos': (), 'aproximacion': None,
            'diagnostico': {'mensaje': str(error), 'campo': captura['modo'], 'fila': None, 'columna': None},
        }
    datos_motor = {
        'matriz_a': sistema.matriz, 'vector_b': sistema.independientes,
        'vector_inicial': captura['vector_inicial'], 'tolerancia': captura['tolerancia'],
        'maximo_iteraciones': _interpretar_maximo(captura['maximo_iteraciones']),
    }
    resultado = resolver_jacobi_desde_captura(datos_motor)
    return {**_serializar(asdict(resultado)), 'variables': sistema.variables}


def _obtener_sistema(captura: dict) -> SistemaCapturado:
    if captura['modo'] == 'ecuaciones':
        return interpretar_ecuaciones(captura['ecuaciones'])
    if captura['matriz_vacia']:
        raise ValueError('Escribe un sistema en la matriz o carga el ejemplo.')
    return SistemaCapturado(captura['matriz_a'], captura['vector_b'], captura['variables'])


def _interpretar_maximo(texto: str) -> int | None:
    try:
        return int(texto.strip()) if len(texto) < 32 else None
    except ValueError:
        return None


def _serializar(valor):
    if isinstance(valor, Fraction):
        return formatear_racional_exacto(valor)
    if isinstance(valor, dict):
        return {clave: _serializar(dato) for clave, dato in valor.items()}
    if isinstance(valor, tuple):
        return tuple(_serializar(dato) for dato in valor)
    return valor
