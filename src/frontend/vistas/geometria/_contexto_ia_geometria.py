"""Contexto y sugerencias de IA para la escena y el resultado vigente."""
from __future__ import annotations

from src.ai.contexto import ContextoIA, EstadoContexto, sanear_cadena_usuario
from src.ai.huellas import esta_desactualizado
from src.frontend.sugerencias import Senales

ESTADOS_SENALES = {
    'SOLUCION_UNICA': 'unica', 'UNICA': 'unica',
    'SIN_SOLUCION': 'sin_solucion',
    'SOLUCIONES_INFINITAS': 'infinita', 'INFINITA': 'infinita',
}


def _extraer_datos_entrada_ia(vista) -> dict:
    carga = vista._construir_carga() or {}
    datos = {'escena': vista.escena}
    if vista.escena == 'rectas-planos':
        datos['matriz_a'] = [[sanear_cadena_usuario(str(valor), 32) for valor in fila]
                             for fila in carga.get('matriz_a', [])]
        datos['vector_b'] = [sanear_cadena_usuario(str(valor), 32) for valor in carga.get('vector_b', [])]
    else:
        datos['vectores'] = [[sanear_cadena_usuario(str(valor), 32) for valor in vector.get('datos', [])]
                            for vector in carga.get('vectores', [])]
        if vista.escena == 'combinacion':
            datos['objetivo'] = [sanear_cadena_usuario(str(valor), 32) for valor in carga.get('objetivo', {}).get('datos', [])]
    return datos


def _extraer_datos_resultado_ia(vista, resultado: dict) -> dict:
    if resultado.get('estado') != 'EXITO':
        return {'estado': 'ERROR', 'mensaje': resultado.get('mensaje', '')}
    datos = {'estado_solucion': resultado.get('estado_solucion', '')}
    if vista.escena == 'rectas-planos':
        conjunto = resultado.get('conjunto_solucion') or {}
        datos['tipo_conjunto_solucion'] = conjunto.get('tipo', '')
        for clave in ('dimension', 'variables_libres'):
            if clave in conjunto:
                datos[clave] = conjunto[clave]
        if resultado.get('parametro_pendiente'):
            datos['pendiente'] = True
    return datos


def obtener_contexto_ia(vista) -> ContextoIA:
    """Describe las entradas y expone solo el resultado que corresponde a ellas."""
    datos = _extraer_datos_entrada_ia(vista)
    contexto = ContextoIA('visualizador', 'Visualizador geométrico', f'Escena: {vista.escena}', datos,
                         estado=EstadoContexto(vacio=vista.ultimo_resultado is None))
    if vista.ultimo_resultado is None:
        return contexto
    entrada = {'escena': vista.escena, 'carga': vista._construir_carga()}
    contexto.desactualizado = esta_desactualizado(entrada, vista._huella_resultado)
    contexto.resultado = None if contexto.desactualizado else _extraer_datos_resultado_ia(vista, vista.ultimo_resultado)
    return contexto


def obtener_senales_ia(vista) -> Senales:
    """Devuelve sugerencias según el estado serializado del controlador."""
    resultado = vista.ultimo_resultado or {}
    if resultado.get('estado') != 'EXITO':
        return Senales(herramienta='visualizador', estado='sin_resultado')
    estado = 'resultado' if vista.escena == 'vectores' else ESTADOS_SENALES.get(resultado.get('estado_solucion'), 'sin_resultado')
    banderas = frozenset(resultado.get('banderas', [])) if vista.escena == 'rectas-planos' else frozenset()
    return Senales(herramienta='visualizador', estado=estado, banderas=banderas)
