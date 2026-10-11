"""Carga de transferencias validadas en controles del visualizador geométrico."""
from __future__ import annotations

from src.backend.geometria.transferencia import validar_transferencia_escena
from src.frontend.componentes.cuadricula_base import DIMENSION_MINIMA, actualizar_estados_botones_dimension
from src.frontend.componentes.vector_capture import DIMENSION_MAXIMA_VECTORES
from src.frontend.componentes.handoff import (
    ResultadoHandoff, consumir_sistema, consumir_vectores,
    renderizar_aviso_handoff, limpiar_url_handoff,
)


def procesar_handoff_rectas(vista, token: str):
    """Carga las ecuaciones transferidas en la cuadrícula y programa su dibujo."""
    resultado = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    if resultado is None:
        return
    limpiar_url_handoff()
    if resultado.status == 'ok' and resultado.data:
        matriz = resultado.data.get('matrix_A', [])
        vector = resultado.data.get('vector_b', [])
        if matriz and vista.cuadricula:
            _prellenar_cuadricula(vista.cuadricula, matriz, vector)
            vista._programar_actualizacion()
        mensaje = f'Sistema cargado desde {resultado.source_name}'
    else:
        mensaje = ''
    with vista.contenedor_estado:
        renderizar_aviso_handoff(resultado, mensaje)


def _prellenar_cuadricula(cuadricula, matriz: list, vector: list):
    cuadricula.m = len(matriz)
    cuadricula.n = len(matriz[0]) if matriz else 2
    cuadricula._cache_A.clear()
    cuadricula._cache_b.clear()
    cuadricula._cache_A.update({(i, j): str(valor) for i, fila in enumerate(matriz) for j, valor in enumerate(fila)})
    cuadricula._cache_b.update({i: str(valor) for i, valor in enumerate(vector)})
    cuadricula.entradas_A.clear()
    cuadricula.entradas_b.clear()
    cuadricula.generar_cuadricula()


def _validar_escena(resultado, escena: str):
    if resultado.status != 'ok' or not resultado.data:
        return resultado
    mensaje = validar_transferencia_escena(escena, resultado.data.get('scene'), resultado.data.get('data', []))
    if mensaje is None:
        return resultado
    return ResultadoHandoff(status='invalid', data=None, source_name=resultado.source_name, message=mensaje)


def procesar_handoff_vectores(vista, token: str):
    """Delega las restricciones y carga los vectores de una transferencia válida."""
    resultado = consumir_vectores(token, allowed_n={2, 3})
    if resultado is None:
        return
    limpiar_url_handoff()
    resultado = _validar_escena(resultado, vista.escena)
    mensaje = ''
    if resultado.status == 'ok':
        _cargar_vectores(vista, resultado.data.get('data', []))
        vista._programar_actualizacion()
        mensaje = f'Vectores cargados desde {resultado.source_name}'
    with vista.contenedor_estado:
        renderizar_aviso_handoff(resultado, mensaje)


def _cargar_vectores(vista, vectores: list):
    panel = vista.panel_vectores if vista.escena == 'vectores' else vista.panel_combinacion
    if not panel or not vectores:
        return
    panel.dim = len(vectores[0])
    if panel.lbl_dim:
        panel.lbl_dim.set_text(str(panel.dim))
    actualizar_estados_botones_dimension(
        panel.btn_dim_dec, panel.btn_dim_inc, panel.dim, DIMENSION_MINIMA, DIMENSION_MAXIMA_VECTORES,
    )
    while len(panel.vectors) < len(vectores):
        panel.add_vector()
    for nombre, coordenadas in zip(panel.vectors, vectores):
        panel.vectors[nombre]['cache'].clear()
        panel.vectors[nombre]['cache'].update({i: str(valor) for i, valor in enumerate(coordenadas)})
    panel.render_all_vectors()
