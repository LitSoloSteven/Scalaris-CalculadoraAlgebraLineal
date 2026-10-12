"""Contexto y sugerencias de IA para la escena y el resultado vigente."""
from __future__ import annotations

from src.ai.contexto import ContextoIA, EstadoContexto, sanear_cadena_usuario
from src.ai.huellas import esta_desactualizado
from src.frontend.suggestions import Signals

ESTADOS_SENALES = {
    'UNIQUE_SOLUTION': 'unique', 'UNIQUE': 'unique',
    'NO_SOLUTION': 'no_solution',
    'INFINITE_SOLUTIONS': 'infinite', 'INFINITE': 'infinite',
}


def _extraer_datos_entrada_ia(vista) -> dict:
    carga = vista._construir_carga() or {}
    datos = {'scene': vista.escena}
    if vista.escena == 'rectas-planos':
        datos['matrix_A'] = [[sanear_cadena_usuario(str(valor), 32) for valor in fila]
                             for fila in carga.get('matrix_A', [])]
        datos['vector_b'] = [sanear_cadena_usuario(str(valor), 32) for valor in carga.get('vector_b', [])]
    else:
        datos['vectors'] = [[sanear_cadena_usuario(str(valor), 32) for valor in vector.get('data', [])]
                            for vector in carga.get('vectors', [])]
        if vista.escena == 'combinacion':
            datos['b'] = [sanear_cadena_usuario(str(valor), 32) for valor in carga.get('b', {}).get('data', [])]
    return datos


def _extraer_datos_resultado_ia(vista, resultado: dict) -> dict:
    if resultado.get('status') != 'OK':
        return {'status': 'ERROR', 'message': resultado.get('message', '')}
    datos = {'solution_status': resultado.get('solution_status', '')}
    if vista.escena == 'rectas-planos':
        conjunto = resultado.get('set') or {}
        datos['set_kind'] = conjunto.get('kind', '')
        for clave in ('dimension', 'free_vars'):
            if clave in conjunto:
                datos[clave] = conjunto[clave]
        if resultado.get('pending_param'):
            datos['pending'] = True
    return datos


def obtener_contexto_ia(vista) -> ContextoIA:
    """Describe las entradas y expone solo el resultado que corresponde a ellas."""
    datos = _extraer_datos_entrada_ia(vista)
    contexto = ContextoIA('visualizador', 'Visualizador geométrico', f'Escena: {vista.escena}', datos,
                         estado=EstadoContexto(vacio=vista.ultimo_resultado is None))
    if vista.ultimo_resultado is None:
        return contexto
    entrada = {'scene': vista.escena, 'payload': vista._construir_carga()}
    contexto.desactualizado = esta_desactualizado(entrada, vista._huella_resultado)
    contexto.resultado = None if contexto.desactualizado else _extraer_datos_resultado_ia(vista, vista.ultimo_resultado)
    return contexto


def obtener_senales_ia(vista) -> Signals:
    """Devuelve sugerencias según el estado serializado del controlador."""
    resultado = vista.ultimo_resultado or {}
    if resultado.get('status') != 'OK':
        return Signals(tool='visualizador', state='none')
    estado = 'result' if vista.escena == 'vectores' else ESTADOS_SENALES.get(resultado.get('solution_status'), 'none')
    banderas = frozenset(resultado.get('flags', [])) if vista.escena == 'rectas-planos' else frozenset()
    return Signals(tool='visualizador', state=estado, flags=banderas)
