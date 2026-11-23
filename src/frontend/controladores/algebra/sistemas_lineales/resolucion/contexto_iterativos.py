"""Contexto pedagógico saneado, vigencia y señales para métodos iterativos."""
from __future__ import annotations

from src.ai.contexto.contexto import (
    ContextoIA,
    EstadoContexto,
    compactar_numero,
    describir_matriz,
    generar_nota_ventana,
    sanear_cadena_usuario,
)
from src.ai.huellas import esta_desactualizado
from src.frontend.nucleo.textos.textos_metodos_iterativos import CAUSAS_PARADA, NOMBRES_METODOS
from src.frontend.presentacion.sugerencias import Senales, primera_celda_invalida

_LIMITE_ECUACION = 120
_LIMITE_CELDA = 32
_LIMITE_NUMERO_RESUMEN = 48
_LIMITE_LINEAS_ECUACIONES = 12
_ESTADOS_SENAL = {
    'SOLUCION_EXACTA': 'solucion_exacta',
    'TOLERANCIA_ALCANZADA': 'tolerancia_alcanzada',
    'MAXIMO_ITERACIONES': 'maximo_iteraciones',
    'LIMITE_ARITMETICO': 'limite_aritmetico',
    'DIAGONAL_NULA': 'diagonal_nula',
    'ENTRADA_INVALIDA': 'entrada_invalida',
}


def entrada_iterativa_actual(vista) -> dict:
    """Devuelve la instantánea completa con el método activo para validar huella."""
    return {**vista.captura.obtener(), 'metodo': vista.metodo}


def resultado_iterativo_vigente(vista) -> dict | None:
    """Devuelve el resultado únicamente si coincide con método y captura vigentes."""
    resultado = getattr(vista, 'ultimo_resultado', None)
    if not resultado or resultado.get('metodo') != vista.metodo:
        return None
    if esta_desactualizado(entrada_iterativa_actual(vista), getattr(vista, '_huella_resultado', None)):
        return None
    return resultado


def _compactar_secuencia(valores: tuple | list, limite: int = _LIMITE_NUMERO_RESUMEN) -> list[str]:
    return [compactar_numero(sanear_cadena_usuario(str(valor), 128), limite) for valor in valores]


def _construir_entrada_saneada(captura: dict) -> tuple[dict, str | None, bool]:
    inicio = _compactar_secuencia(captura['vector_inicial'], _LIMITE_CELDA)
    parametros = {
        'vector_inicial': {'orientacion': 'columna', 'datos': inicio},
        'tolerancia': sanear_cadena_usuario(captura['tolerancia'], _LIMITE_CELDA),
        'maximo_iteraciones': sanear_cadena_usuario(captura['maximo_iteraciones'], _LIMITE_CELDA),
    }
    if captura['modo'] == 'ecuaciones':
        lineas = [
            sanear_cadena_usuario(linea, _LIMITE_ECUACION)
            for linea in str(captura['ecuaciones']).splitlines() if linea.strip()
        ][:_LIMITE_LINEAS_ECUACIONES]
        return {'ecuaciones': lineas, **parametros}, None, not str(captura['ecuaciones']).strip()
    datos_a = [[sanear_cadena_usuario(celda, _LIMITE_CELDA) for celda in fila] for fila in captura['matriz_a']]
    datos_b = [[sanear_cadena_usuario(celda, _LIMITE_CELDA)] for celda in captura['vector_b']]
    descriptor_a = describir_matriz(datos_a)
    descriptor_b = describir_matriz(datos_b)
    variables = [sanear_cadena_usuario(nombre, _LIMITE_CELDA) for nombre in captura['variables']]
    entrada = {'A': descriptor_a, 'b': descriptor_b, 'variables': variables, **parametros}
    return entrada, generar_nota_ventana(descriptor_a, descriptor_b), bool(captura['matriz_vacia'])


def _agregar_magnitudes_iterativas(resumen: dict, resultado: dict, pasos: tuple | list) -> None:
    for clave in ('aproximacion', 'residuo'):
        if resultado.get(clave) is not None:
            resumen[clave] = _compactar_secuencia(resultado[clave])
    if resultado.get('norma_residuo') is not None:
        resumen['norma_residuo'] = compactar_numero(str(resultado['norma_residuo']), _LIMITE_NUMERO_RESUMEN)
    if pasos and pasos[-1].get('norma_cambio') is not None:
        resumen['norma_cambio_ultimo_barrido'] = compactar_numero(
            str(pasos[-1]['norma_cambio']), _LIMITE_NUMERO_RESUMEN,
        )


def _resumir_resultado_iterativo(resultado: dict) -> dict:
    codigo = str(resultado.get('codigo', 'ENTRADA_INVALIDA'))
    veredicto = CAUSAS_PARADA.get(codigo, codigo)
    pasos = resultado.get('pasos', ())
    variables = [sanear_cadena_usuario(str(nombre), _LIMITE_CELDA) for nombre in resultado.get('variables', ())]
    resumen = {
        'metodo': NOMBRES_METODOS.get(resultado.get('metodo'), str(resultado.get('metodo', ''))),
        'estado': codigo, 'veredicto': veredicto, 'mensaje': veredicto,
        'causa_parada': codigo, 'criterio_parada': 'norma_infinito_residuo',
        'barridos': len(pasos), 'variables': variables,
    }
    _agregar_magnitudes_iterativas(resumen, resultado, pasos)
    entrada_canonica = resultado.get('entrada_canonica')
    if isinstance(entrada_canonica, dict) and entrada_canonica.get('tolerancia') is not None:
        resumen['tolerancia'] = compactar_numero(str(entrada_canonica['tolerancia']), _LIMITE_CELDA)
    if resultado.get('dominancia_estricta') is not None:
        resumen['dominancia_estricta'] = bool(resultado['dominancia_estricta'])
    diagnostico = resultado.get('diagnostico')
    if isinstance(diagnostico, dict) and diagnostico.get('mensaje'):
        resumen['diagnostico'] = sanear_cadena_usuario(diagnostico['mensaje'], 160)
    return resumen


def obtener_contexto_iterativo(vista) -> ContextoIA:
    """Construye el contexto saneado de Glosa omitiendo resultados obsoletos o ajenos."""
    captura = vista.captura.obtener()
    solicitud = {**captura, 'metodo': vista.metodo}
    entrada, nota_ventana, vacio = _construir_entrada_saneada(captura)
    huella = getattr(vista, '_huella_resultado', None)
    ultimo = getattr(vista, 'ultimo_resultado', None)
    desactualizado = esta_desactualizado(solicitud, huella) or bool(ultimo and ultimo.get('metodo') != vista.metodo)
    resumen = None if (desactualizado or not ultimo) else _resumir_resultado_iterativo(ultimo)
    return ContextoIA(
        'metodos_iterativos',
        'Métodos iterativos',
        NOMBRES_METODOS[vista.metodo],
        entrada,
        EstadoContexto(resultado=resumen, nota_ventana=nota_ventana, desactualizado=desactualizado, vacio=vacio),
    )


def _celdas_iterativas(captura: dict) -> list[tuple]:
    elementos: list[tuple] = []
    if captura['modo'] == 'matriz':
        for indice_fila, fila in enumerate(captura['matriz_a']):
            for indice_columna, valor in enumerate(fila):
                elementos.append((f'A[{indice_fila + 1},{indice_columna + 1}]', valor, (indice_fila, indice_columna)))
        for indice_fila, valor in enumerate(captura['vector_b']):
            elementos.append((f'b[{indice_fila + 1}]', valor, (indice_fila, len(captura['matriz_a']))))
    for indice, valor in enumerate(captura['vector_inicial']):
        elementos.append((f'x0[{indice + 1}]', valor, None))
    elementos.append(('tolerancia', captura['tolerancia'], None))
    elementos.append(('maximo', captura['maximo_iteraciones'], None))
    return elementos


def obtener_senales_iterativo(vista) -> Senales:
    """Emite el estado, la primera celda inválida y las banderas del cálculo vigente."""
    captura = vista.captura.obtener()
    vigente = resultado_iterativo_vigente(vista)
    banderas = {vista.metodo.replace('-', '_')}
    estado = 'sin_resultado'
    if vigente is not None:
        estado = _ESTADOS_SENAL.get(vigente.get('codigo', ''), 'sin_resultado')
        if vigente.get('dominancia_estricta') is False:
            banderas.add('sin_dominancia')
        if vigente.get('aproximacion') is not None and not vigente.get('pasos'):
            banderas.add('cero_barridos')
    return Senales(
        herramienta='metodos_iterativos',
        estado=estado,
        banderas=frozenset(banderas),
        invalida=primera_celda_invalida(_celdas_iterativas(captura)),
    )
