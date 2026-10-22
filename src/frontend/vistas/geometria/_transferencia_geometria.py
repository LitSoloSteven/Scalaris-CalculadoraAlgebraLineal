"""Carga de transferencias validadas en controles del visualizador geométrico."""
from __future__ import annotations

from src.backend.geometria.transferencia import validar_transferencia_escena
from src.frontend.componentes.cuadricula_base import DIMENSION_MINIMA, actualizar_estados_botones_dimension
from src.backend.constantes import DIMENSION_MAXIMA_VECTORES
from src.frontend.componentes.transferencia import (
    ResultadoTransferencia, consumir_sistema, consumir_vectores,
    renderizar_aviso_transferencia, limpiar_url_transferencia,
)


def procesar_transferencia_rectas(vista, token: str):
    """Carga las ecuaciones transferidas en la cuadrícula y programa su dibujo."""
    resultado = consumir_sistema(token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    if resultado is None:
        return
    limpiar_url_transferencia()
    if resultado.estado == 'exito' and resultado.datos:
        matriz = resultado.datos.get('matriz_a', [])
        vector = resultado.datos.get('vector_b', [])
        if matriz and vista.cuadricula:
            _prellenar_cuadricula(vista.cuadricula, matriz, vector)
            vista._programar_actualizacion()
        mensaje = f'Sistema cargado desde {resultado.nombre_origen}'
    else:
        mensaje = ''
    with vista.contenedor_estado:
        renderizar_aviso_transferencia(resultado, mensaje)


def _prellenar_cuadricula(cuadricula, matriz: list, vector: list):
    cuadricula.filas = len(matriz)
    cuadricula.columnas = len(matriz[0]) if matriz else 2
    cuadricula._cache_coeficientes.clear()
    cuadricula._cache_independientes.clear()
    cuadricula._cache_coeficientes.update({(i, j): str(valor) for i, fila in enumerate(matriz) for j, valor in enumerate(fila)})
    cuadricula._cache_independientes.update({i: str(valor) for i, valor in enumerate(vector)})
    cuadricula.entradas_coeficientes.clear()
    cuadricula.entradas_independientes.clear()
    cuadricula.generar_cuadricula()


def _validar_escena(resultado, escena: str):
    if resultado.estado != 'exito' or not resultado.datos:
        return resultado
    mensaje = validar_transferencia_escena(escena, resultado.datos.get('escena'), resultado.datos.get('vectores', []))
    if mensaje is None:
        return resultado
    return ResultadoTransferencia(estado='invalida', datos=None, nombre_origen=resultado.nombre_origen, mensaje=mensaje)


def procesar_transferencia_vectores(vista, token: str):
    """Delega las restricciones y carga los vectores de una transferencia válida."""
    resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})
    if resultado is None:
        return
    limpiar_url_transferencia()
    resultado = _validar_escena(resultado, vista.escena)
    mensaje = ''
    if resultado.estado == 'exito':
        _cargar_vectores(vista, resultado.datos.get('vectores', []))
        vista._programar_actualizacion()
        mensaje = f'Vectores cargados desde {resultado.nombre_origen}'
    with vista.contenedor_estado:
        renderizar_aviso_transferencia(resultado, mensaje)


def _cargar_vectores(vista, vectores: list):
    panel = vista.panel_vectores if vista.escena == 'vectores' else vista.panel_combinacion
    if not panel or not vectores:
        return
    panel.dimension = len(vectores[0])
    if panel.etiqueta_dimension:
        panel.etiqueta_dimension.set_text(str(panel.dimension))
    actualizar_estados_botones_dimension(
        panel.boton_reducir_dimension, panel.boton_aumentar_dimension, panel.dimension, DIMENSION_MINIMA, DIMENSION_MAXIMA_VECTORES,
    )
    while len(panel.vectores) < len(vectores):
        panel.agregar_vector()
    for nombre, coordenadas in zip(panel.vectores, vectores):
        panel.vectores[nombre]['celdas'].clear()
        panel.vectores[nombre]['celdas'].update({i: str(valor) for i, valor in enumerate(coordenadas)})
    panel.renderizar_todos_vectores()
