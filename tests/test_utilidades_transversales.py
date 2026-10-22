"""Regresiones de las capturas, avisos y decisiones compartidas entre herramientas."""
import asyncio
import json
from fractions import Fraction
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from nicegui import ui

from src.ai.clasificador_respuestas import ContextoIntento, clasificar_error_http
from src.ai.huellas import calcular_huella
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.formateadores import (
    formatear_combinacion_lineal_vector, formatear_expresion_lineal,
)
from src.frontend.componentes.avisos_resultado import mostrar_error_inesperado
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.controladores.captura_contexto import capturar_bases, capturar_matrices, capturar_romanos
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from src.frontend.controladores.utilidades import extraer_datos_matriz, parsear_carga_json
from src.frontend.componentes.glosa_preguntas import PreguntasGlosaMixin
from src.frontend.componentes.glosa_panel_lateral import PanelLateralGlosaMixin
from tests.comun import RAIZ
from tests.comun_clientes import ClienteSimulado
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('codigo', [429, 503])
@pytest.mark.parametrize('intento,modelo,tiempo,accion', [
    (0, 0, 8.001, 'reintentar'), (0, 0, 8, 'reserva'),
    (1, 0, 30, 'reserva'), (0, 1, 30, 'terminar'),
])
def test_reintento_compartido_conserva_el_plazo(codigo, intento, modelo, tiempo, accion):
    """El reintento exige el primer modelo, primer intento y más de ocho segundos."""
    resultado, decision = clasificar_error_http(codigo, 'modelo', ContextoIntento(intento, modelo, tiempo, 2))
    assert decision == (accion if codigo == 429 else 'reserva' if accion == 'terminar' else accion)
    assert (resultado is not None) == (codigo == 429 and accion == 'terminar')


def test_captura_matricial_copia_celdas_y_preserva_exactitud():
    """Cambiar el caché después de calcular no cambia la huella de la captura anterior."""
    matrices = {'A': {'cache': {(0, 0): '1/1009'}}}
    captura = capturar_matrices(matrices, ' A+A ')
    huella = calcular_huella(captura)
    matrices['A']['cache'][(0, 0)] = '2/1009'
    assert captura == {'matrices': {'A': {(0, 0): '1/1009'}}, 'expresion': 'A+A'}
    assert calcular_huella(captura) == huella
    assert calcular_huella(capturar_matrices(matrices, 'A+A')) != huella
    assert capturar_matrices({}, None) == {'matrices': {}, 'expresion': ''}


def test_capturas_numericas_preservan_sus_politicas():
    """Bases conserva espacios; romanos normaliza letras y separadores exteriores."""
    vista = SimpleNamespace(base_activa='binario', base_destino='decimal')
    assert capturar_bases(vista, ' 101 ') == {'valor': ' 101 ', 'base_origen': 'binario', 'base_destino': 'decimal'}
    assert capturar_romanos(' xiv ', None, 'resta') == {'a': 'XIV', 'b': '', 'operacion': 'resta'}


def test_lectura_matricial_independiente_con_fraccion_larga():
    """La lectura devuelve filas independientes sin aproximar la matriz original."""
    matriz = Matriz(2, 1, [[Fraction(1, 1009)], [Fraction(-2, 3)]])
    datos = extraer_datos_matriz(matriz)
    datos[0][0] = 0
    assert matriz.obtener(0, 0) == Fraction(1, 1009)
    assert datos[1] == [Fraction(-2, 3)]


def test_notificacion_contexto_opcional():
    """Notifica una sola vez y admite vistas aún sin panel o con un panel incompleto."""
    for vista in (SimpleNamespace(), SimpleNamespace(panel_ia=None), SimpleNamespace(panel_ia=object())):
        actualizar_contexto(vista)
    notificar = Mock()
    actualizar_contexto(SimpleNamespace(panel_ia=SimpleNamespace(programar_actualizacion_contexto=notificar)))
    notificar.assert_called_once_with()


def test_accion_glosa_sin_panel_y_metadatos_no_mutables():
    """La posición actual prevalece sobre metadatos antiguos sin modificar la captura."""
    assert crear_accion_explicacion(None, []) is None
    recibidos = []
    metadatos = {'indice': 99, 'total': 99, 'tipo': 'operacion'}
    paso = SimpleNamespace(indice=0, meta_explicar=metadatos)
    pasos = [paso]
    accion = crear_accion_explicacion(SimpleNamespace(disparar_explicacion_paso=recibidos.append), pasos)
    pasos.append(paso)
    accion(paso)
    assert recibidos == [{'indice': 1, 'total': 2, 'tipo': 'operacion'}]
    assert metadatos == {'indice': 99, 'total': 99, 'tipo': 'operacion'}


@pytest.mark.parametrize('coeficientes,esperado', [
    ([], '0'), ([0, 0], '0'), ([-1, 2], '-x + 2 y'), ([1, -1], 'x - y'),
])
def test_signos_compartidos_preservan_espacios(coeficientes, esperado):
    """La extracción conserva signos, ceros y separación de términos escalares."""
    assert formatear_expresion_lineal(coeficientes, ['x', 'y']) == esperado
    assert formatear_combinacion_lineal_vector([-1, 2], ['u', 'v']) == r'-\mathbf{u} + 2\mathbf{v}'


def test_json_invalido_orienta_sin_mensaje_ingles_del_analizador():
    """El fallo informa línea y columna en español sin publicar la entrada recibida."""
    datos, error = parsear_carga_json('{"privado": SECRETO}')
    mensaje = json.loads(error)['mensaje']
    assert datos is None
    assert 'línea 1, columna 13' in mensaje and 'Revisa' in mensaje
    assert 'SECRETO' not in mensaje and 'Expecting' not in mensaje


def test_aviso_compartido_con_panel_montado_y_eliminado(monkeypatch):
    """El aviso reemplaza resultados y omite toda escritura tras eliminar el contenedor."""
    async def comprobar(vista, cliente):
        """Ejercita el contenedor real y conserva su orientación y texto accesible."""
        mostrar_error_inesperado(vista.contenedor_resultados)
        etiquetas = [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert len(etiquetas) == 1 and 'Revisa los datos' in etiquetas[0]
        vista.contenedor_resultados.delete()
        mostrar_error_inesperado(vista.contenedor_resultados)
    asyncio.run(construir_pagina(monkeypatch, 'matrices', comprobar))


@pytest.mark.parametrize('accion', ['preguntar_sugerencia', 'preguntar_seguimiento', 'disparar_explicacion_paso'])
def test_consultas_ocupadas_comparten_guardia(monkeypatch, accion):
    """Todas las entradas rechazan consultas paralelas antes de iniciar otra tarea."""
    notificar = Mock()
    monkeypatch.setattr(ui, 'notify', notificar)
    panel = PreguntasGlosaMixin()
    panel._esta_enviando = True
    panel._lanzar_tarea = Mock()
    getattr(panel, accion)(object())
    notificar.assert_called_once_with('Glosa está respondiendo. Espera a que termine.', type='warning')
    panel._lanzar_tarea.assert_not_called()


def test_carpeta_recursos_y_url_publica_se_resuelven_juntas():
    """La ruta pública de recursos conserva un único directorio físico canónico."""
    from src.frontend.aplicacion import DIRECTORIO_RECURSOS
    assert DIRECTORIO_RECURSOS == RAIZ / 'src/frontend/recursos'
    assert not (RAIZ / 'src/frontend/assets').exists()
    assert (DIRECTORIO_RECURSOS / 'LogoOscuro.png').is_file()
    assert not (DIRECTORIO_RECURSOS / 'js/square_matrix.js').exists()


def test_envio_comun_espera_la_consulta_en_el_cliente():
    """El envío espera su tarea y conserva el contexto y texto del cliente que lo inicia."""
    async def comprobar():
        """Envía el campo capturado mediante el lanzador real sin contactar servicios externos."""
        panel = PanelLateralGlosaMixin()
        cliente = ClienteSimulado()
        panel._cliente = cliente
        panel.campo_entrada = SimpleNamespace(value='Explica 1/1009')
        panel._enviar_consulta = AsyncMock()
        await panel.enviar_mensaje()
        panel._enviar_consulta.assert_awaited_once_with('Explica 1/1009')
        assert cliente.entradas == 1 and cliente.salidas == 1
    asyncio.run(comprobar())
