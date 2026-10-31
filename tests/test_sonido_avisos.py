"""Contrato del emisor de sonido, notificaciones y control de silencio."""
import ast
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import Client, core, ui

from src.frontend.componentes import sonido
from src.frontend.componentes.control_sonido import renderizar_control_sonido
from src.frontend.componentes.barra_navegacion import crear_barra_navegacion
from src.frontend.vistas.inicio.vista_inicio import VistaInicio
from src.frontend.tema import _CABECERA_HTML
from src.frontend.recursos_vistas import seleccionar_recursos
from tests.comun import RAIZ


@pytest.mark.parametrize('nombre', ['accion', 'navegacion', 'apertura', 'cierre', 'exito', 'aviso', 'error'])
def test_emision_solo_envia_nombre_conocido_al_cliente_conectado(monkeypatch, nombre):
    """El helper encola una llamada segura sin esperar una respuesta de audio."""
    cliente = SimpleNamespace(is_deleted=False, has_socket_connection=True, run_javascript=Mock())
    monkeypatch.setattr(sonido, 'context', SimpleNamespace(client=cliente))
    assert sonido.emitir_sonido(nombre)
    cliente.run_javascript.assert_called_once_with(
        f'window.scalaris?.sonido?.reproducir({json.dumps(nombre)});')


@pytest.mark.parametrize('borrado, conectado', [(True, True), (False, False), (True, False)])
def test_cliente_ausente_no_recibe_sonidos_tardios(monkeypatch, borrado, conectado):
    """Un cliente desconectado o borrado no conserva señales pendientes de otra interacción."""
    cliente = SimpleNamespace(is_deleted=borrado, has_socket_connection=conectado, run_javascript=Mock())
    monkeypatch.setattr(sonido, 'context', SimpleNamespace(client=cliente))
    assert not sonido.emitir_sonido('exito')
    cliente.run_javascript.assert_not_called()


@pytest.mark.parametrize('nombre', ['inexistente', '__proto__', 'exito");alert(1);//', ''])
def test_nombre_no_permitido_no_genera_javascript(monkeypatch, nombre):
    """Los nombres externos no se interpolan ni requieren un cliente activo."""
    cliente = SimpleNamespace(is_deleted=False, has_socket_connection=True, run_javascript=Mock())
    monkeypatch.setattr(sonido, 'context', SimpleNamespace(client=cliente))
    assert not sonido.emitir_sonido(nombre)
    cliente.run_javascript.assert_not_called()


def test_perder_contexto_o_conexion_no_interrumpe_presentacion(monkeypatch):
    """Un error de ciclo de vida durante el envío de una señal se degrada sin audio."""
    cliente = SimpleNamespace(is_deleted=False, has_socket_connection=True,
                              run_javascript=Mock(side_effect=RuntimeError('Desconectado')))
    monkeypatch.setattr(sonido, 'context', SimpleNamespace(client=cliente))
    assert not sonido.emitir_sonido('aviso')


@pytest.mark.parametrize('tipo, esperado', [('positive', 'exito'), ('negative', 'error'),
                                         ('warning', 'aviso'), ('info', 'aviso'), (None, 'aviso')])
def test_notificacion_conserva_argumentos_retorno_y_texto(monkeypatch, tipo, esperado):
    """El mensaje se presenta sin transformaciones y se acompaña de la categoría correcta."""
    retorno = object()
    notificacion = Mock(return_value=retorno)
    emision = Mock()
    monkeypatch.setattr(sonido.ui, 'notify', notificacion)
    monkeypatch.setattr(sonido, 'emitir_sonido', emision)
    opciones = {'position': 'top', 'timeout': 2500}
    if tipo:
        opciones['type'] = tipo
    assert sonido.notificar('Revisa <A> y vuelve a calcular.', **opciones) is retorno
    notificacion.assert_called_once_with('Revisa <A> y vuelve a calcular.', **opciones)
    emision.assert_called_once_with(esperado)


def test_los_avisos_python_tienen_un_unico_emisor():
    """Ningún consumidor evita la utilidad común de notificación."""
    emisores = []
    for ruta in (RAIZ / 'src/frontend').rglob('*.py'):
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding='utf-8'))):
            if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                    and isinstance(nodo.func.value, ast.Name)
                    and nodo.func.value.id == 'ui' and nodo.func.attr == 'notify'):
                emisores.append(ruta.relative_to(RAIZ).as_posix())
    assert emisores == ['src/frontend/componentes/sonido.py']


def test_control_nativo_con_nombre_estable_estado_e_iconos(monkeypatch):
    """El botón ofrece activación nativa de teclado sin depender de callbacks del servidor."""
    monkeypatch.setattr(core, 'script_mode', False)
    cliente = Client(ui.page('/prueba_control_sonido'))
    try:
        with cliente:
            boton = renderizar_control_sonido()
        assert boton.tag == 'button'
        assert boton._props['type'] == 'button'
        assert boton._props['aria-label'] == 'Silenciar sonidos'
        assert boton._props['aria-pressed'] == 'false'
        assert 'data-sonido-control' in boton._props
        assert not boton._event_listeners
        iconos = [elemento for elemento in boton.descendants() if 'data-sonido-icono' in elemento._props]
        assert len(iconos) == 2
        assert all(elemento._props['aria-hidden'] == 'true' for elemento in iconos)
        assert iconos[1]._props['hidden'] is True
    finally:
        cliente.delete()


@pytest.mark.parametrize('actualizada', [True, False])
def test_navegacion_e_inicio_montan_el_mismo_control(monkeypatch, actualizada):
    """Las variantes de navegación y la cabecera inicial permiten cambiar el silencio."""
    monkeypatch.setattr(core, 'script_mode', False)
    monkeypatch.setattr('src.frontend.componentes.barra_navegacion.banderas.navegacion_actualizada', lambda: actualizada)
    cliente = Client(ui.page('/prueba_sonido_navegacion'))
    try:
        with cliente:
            crear_barra_navegacion(ruta_activa='/algebra-lineal/sistemas')
            VistaInicio()._renderizar_cabecera()
        controles = [elemento for elemento in cliente.elements.values() if 'data-sonido-control' in elemento._props]
        assert len(controles) == 2
    finally:
        cliente.delete()


@pytest.mark.parametrize('vista', ['inicio', 'sistemas', 'vectores', 'matrices', 'inversa',
                                 'determinantes', 'factorizacion_lu', 'bases', 'romanos',
                                 'visualizador', 'leontief', 'transformaciones'])
def test_recursos_sonoros_se_cargan_una_vez_en_todas_las_vistas(vista):
    """La selección de recursos conserva el orden de motor, preferencia y consumidores."""
    nombres = ['catalogo_sonidos.js', 'sonido.js', 'preferencia_sonido.js', 'interacciones_sonoras.js']
    cabecera = seleccionar_recursos(_CABECERA_HTML, vista)
    posiciones = [cabecera.index('/assets/js/' + nombre) for nombre in nombres]
    assert posiciones == sorted(posiciones)
    assert all(cabecera.count('/assets/js/' + nombre) == 1 for nombre in nombres)
