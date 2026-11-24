"""Integración de navegación, recursos, regresión y accesibilidad en los tres módulos."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.componentes.aplicacion.controles.barra_navegacion import _clave_reciente_valida
from src.frontend.controladores.inicio._recientes import normalizar_recientes
from src.frontend.navegacion import herramienta_por_identificador, ruta_de
from src.frontend.presentacion import tema
from src.frontend.presentacion.recursos_vistas import seleccionar_recursos
from tests.comun import RAIZ
from tests.comun_calculos_vistas import calcular_minimo
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


@pytest.fixture(autouse=True)
def registrar_vistas_nuevas(monkeypatch):
    """Incluye las vistas nuevas en el mapa compartido de pruebas."""
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))
    monkeypatch.setitem(VISTAS_RUTAS, 'espacios_subespacios', (
        'algebra.operaciones_vectores.vista_espacios_subespacios', 'VistaEspaciosSubespacios',
    ))


@pytest.mark.parametrize('nav', ['1', '0'])
@pytest.mark.parametrize('herramienta,esperado', [
    ('metodos_iterativos', 'Jacobi | Scalaris'),
    ('espacios_subespacios', 'Espacios y subespacios | Scalaris'),
])
def test_navegacion_titulos_recientes_y_enlace_inicio(monkeypatch, nav, herramienta, esperado):
    """Verifica ambos modos de barra, enlace a inicio, reciente y descriptor."""
    monkeypatch.setenv('SCALARIS_NAV', nav)

    async def comprobar(vista, cliente):
        """Valida título, barra activa, logotipo/inicio y llamada a recientes."""
        titulo_catalogo = 'Métodos iterativos | Scalaris' if herramienta == 'metodos_iterativos' else esperado
        assert herramienta_por_identificador(herramienta).titulo_pagina == titulo_catalogo
        if herramienta == 'metodos_iterativos':
            assert cliente.title == esperado
            vista.selector_metodo.set_value('gauss-seidel')
            assert cliente.title == 'Gauss-Seidel | Scalaris'
        activos = [
            elemento._props.get('href')
            for elemento in cliente.elements.values()
            if elemento._props.get('aria-current') == 'page'
        ]
        assert activos == [ruta_de(herramienta)]
        enlaces_inicio = [
            elemento for elemento in cliente.elements.values()
            if elemento._props.get('href') == '/' or getattr(elemento, '_props', {}).get('aria-label', '').startswith('Scalaris')
        ]
        assert enlaces_inicio

    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
    assert 'Jacobi y Gauss-Seidel' in herramienta_por_identificador('metodos_iterativos').descriptor
    assert _clave_reciente_valida(ruta_de(herramienta), None) == herramienta
    assert [item.identificador for item in normalizar_recientes([herramienta])] == [herramienta]


def test_aislamiento_recursos_y_presencia_de_sonido():
    """Cada página carga el motor sonoro y excluye scripts y CSS de otras vistas."""
    sonidos = ('catalogo_sonidos.js', 'sintesis_sonora.js', 'asignacion_sonora.js', 'eventos_sonoros.js')
    cab_iter = seleccionar_recursos(tema._CABECERA_HTML, 'metodos_iterativos')
    cab_sub = seleccionar_recursos(tema._CABECERA_HTML, 'espacios_subespacios')
    cab_sis = seleccionar_recursos(tema._CABECERA_HTML, 'sistemas')
    for sonido in sonidos:
        assert sonido in cab_iter and sonido in cab_sub
    assert 'iterativos_historial.js' in cab_iter and 'iterativos_historial.js' not in cab_sub
    assert 'vistas_metodos_iterativos.css' in cab_iter and 'vistas_metodos_iterativos.css' not in cab_sis
    assert 'vistas_subespacios.css' in cab_sub and 'vistas_subespacios.css' not in cab_iter
    assert 'sistemas_metodo.js' in cab_sis and 'sistemas_metodo.js' not in cab_iter
    for prohibido in ('inicio.js', 'vistas_inicio_directorio.css', 'sincronizacion_diseno.js'):
        assert prohibido not in cab_iter and prohibido not in cab_sub


@pytest.mark.parametrize('herramienta,parametros', [
    ('sistemas', {'method': 'gauss'}),
    ('sistemas', {'method': 'gauss-jordan'}),
    ('vectores', None),
    ('visualizador', None),
])
def test_regresion_rutas_existentes_con_glosa_y_pdf(monkeypatch, herramienta, parametros):
    """Sistemas, Vectores y Visualizador conservan cálculo, Glosa y exportación PDF."""
    async def comprobar(vista, _cliente):
        """Ejecuta cálculo mínimo y comprueba que sigue vigente."""
        await calcular_minimo(herramienta, vista)
        if herramienta == 'visualizador':
            assert vista.escena == 'rectas-planos'
        else:
            assert vista.actualizar_exportacion_pdf is not None
        assert vista.obtener_contexto_ia() is not None

    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar, parametros))


def test_maximo_pasos_pegado_y_accesibilidad_css(monkeypatch):
    """Soporta 100 barridos, pegado compartido y contratos de movimiento reducido y dvh."""
    async def comprobar(vista, cliente):
        """Resuelve 100 barridos exactos y comprueba tabla y atributos accesibles."""
        assert 'cuadricula_compartida.js' in cliente.head_html
        vista.captura.selector.set_value('ecuaciones')
        vista.captura.ecuaciones.set_value('2*x1 + x2 = 3\nx1 + 2*x2 = 3')
        vista.captura.tolerancia.set_value('1/1000000000000000000000000000000000000000000')
        vista.captura.maximo.set_value('100')
        await vista.resolver()
        assert vista.ultimo_resultado['codigo'] == 'MAXIMO_ITERACIONES'
        assert len(vista.reproductor_pasos.pasos) == 100
        assert vista.estado._props.get('role') == 'status'
        assert vista.estado._props.get('aria-live') == 'polite'
        vista.captura.selector.set_value('matriz')
        vista.captura.cuadricula.cargar_datos([['8', '-1', '1'], ['2', '10', '-1'], ['1', '-1', '6']], ['5', '23', '-7'])
        assert len(vista.captura.obtener()['matriz_a']) == 3

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar))
    css_iter = (RAIZ / 'src/frontend/recursos/css/algebra/espacios/vistas_metodos_iterativos.css').read_text(encoding='utf-8')
    css_sub = (RAIZ / 'src/frontend/recursos/css/algebra/espacios/vistas_subespacios.css').read_text(encoding='utf-8')
    assert 'tabular-nums' in css_iter and 'tabular-nums' in css_sub
    assert 'dvh' in css_sub and '100vh' not in css_sub
    assert 'prefers-reduced-motion: reduce' in css_sub
