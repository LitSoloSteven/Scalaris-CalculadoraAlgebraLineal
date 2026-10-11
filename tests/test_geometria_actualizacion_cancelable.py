"""Regresiones de cancelación, confirmación, errores y representación segura."""
import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from nicegui import ui

from src.frontend.vistas.geometria import _actualizacion_geometria as actualizacion
from src.frontend.vistas.geometria import _resumen_geometria as resumen
from src.frontend.vistas.geometria._contexto_ia_geometria import obtener_contexto_ia
from src.frontend.vistas.geometria.vista_geometria import VistaGeometria
from src.frontend.controladores.geometria import selector_celda_error
from tests.comun import RAIZ
from tests.rutas_auditadas import RUTAS_AUDITADAS


def _crear_vista_simulada(monkeypatch):
    vista = VistaGeometria()
    vista.panel_ia = MagicMock()
    monkeypatch.setattr(vista, '_construir_carga', lambda: {'matrix_A': [['1', '0']], 'vector_b': ['1']})
    monkeypatch.setattr(vista, '_construir_deslizador', MagicMock())
    monkeypatch.setattr(vista, '_renderizar_resumen', MagicMock())
    monkeypatch.setattr(vista, '_renderizar_error', MagicMock())
    return vista


def test_cancelacion_no_confirma_resultado_tardio(monkeypatch):
    """Una actualización cancelada antes del resultado no registra datos obsoletos."""
    async def comprobar():
        vista = _crear_vista_simulada(monkeypatch)
        iniciado = asyncio.Event()

        async def esperar_resultado(*args):
            iniciado.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(actualizacion, 'ejecutar_controlador_geometria', esperar_resultado)
        tarea = asyncio.create_task(vista._actualizar_figura())
        await iniciado.wait()
        tarea.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarea
        assert vista.ultimo_resultado is None
        assert vista.ultimo_hash_entrada is None
        vista._renderizar_resumen.assert_not_called()
        vista._renderizar_error.assert_not_called()
    asyncio.run(comprobar())


def test_entrada_identica_no_repite_calculo_confirmado(monkeypatch):
    """Una entrada confirmada evita repetir el trabajador y conserva su resumen."""
    async def comprobar():
        vista = _crear_vista_simulada(monkeypatch)
        resultado = {'status': 'OK', 'n': 2, 'solution_status': 'UNIQUE_SOLUTION'}
        trabajador = AsyncMock(return_value=resultado)
        monkeypatch.setattr(actualizacion, 'ejecutar_controlador_geometria', trabajador)
        monkeypatch.setattr(vista, '_construir_figura', AsyncMock(return_value=True))
        await vista._actualizar_figura()
        await vista._actualizar_figura()
        trabajador.assert_awaited_once()
        assert vista.ultimo_resultado == resultado
        assert vista.ultimo_hash_entrada is not None
        assert vista._primer_dibujo is False
        vista._renderizar_resumen.assert_called_once_with(resultado, 'rectas-planos')
    asyncio.run(comprobar())


def test_debounce_cancela_tarea_anterior(monkeypatch):
    """La programación repetida conserva solo la última tarea de actualización."""
    async def comprobar():
        vista = VistaGeometria()
        ejecutar = AsyncMock()
        monkeypatch.setattr(vista, '_actualizar_figura', ejecutar)
        monkeypatch.setattr('src.frontend.vistas.geometria.vista_geometria.DEBOUNCE_GEOMETRIA_SEGUNDOS', 0)
        vista._programar_actualizacion()
        anterior = vista._tarea_previa
        vista._programar_actualizacion()
        await vista._tarea_previa
        assert anterior.cancelled()
        ejecutar.assert_awaited_once()
    asyncio.run(comprobar())


def test_formulas_escapan_texto_no_confiable(monkeypatch):
    """El texto de una fórmula no puede introducir etiquetas ni eventos HTML."""
    vista = VistaGeometria()
    salida = MagicMock()
    monkeypatch.setattr(ui, 'html', salida)
    resumen._mostrar_formula(vista, '<img src=x onerror=alert(1)> & "', 'ecuacion')
    contenido = salida.call_args.args[0]
    assert '<img' not in contenido
    assert '&lt;img' in contenido
    assert '&amp;' in contenido
    assert '&quot;' in contenido


@pytest.mark.parametrize('escena,nombre', [('vectores', 'u'), ('combinacion', 'b')])
def test_selector_error_corresponde_a_celda_real(escena, nombre):
    """Los atributos de la celda coinciden con el selector emitido por el controlador."""
    vista = VistaGeometria()
    vista.contenedor_controles = ui.column()
    vista._construir_controles(escena)
    panel = vista.panel_vectores if escena == 'vectores' else vista.panel_combinacion
    entradas = [elemento for elemento in panel.vectors[nombre]['ui_container'].descendants() if isinstance(elemento, ui.input)]
    identificador = entradas[1]._props['data-geometria-vector']
    indice = entradas[1]._props['data-geometria-indice']
    selector = selector_celda_error({'kind': 'vec', 'name': nombre, 'index': 1}, escena=escena)
    assert selector == f'input[data-geometria-vector="{identificador}"][data-geometria-indice="{indice}"]'
    vista.contenedor_controles.delete()


def test_contexto_vectores_contiene_entrada_actual(monkeypatch):
    """Glosa recibe las componentes capturadas incluso antes de confirmar el dibujo."""
    vista = VistaGeometria()
    vista.escena = 'vectores'
    monkeypatch.setattr(vista, '_construir_carga', lambda: {'vectors': [{'data': ['1/3', '2']}, {'data': ['4', '5']}]})
    contexto = obtener_contexto_ia(vista)
    assert contexto.input['vectors'] == [['1/3', '2'], ['4', '5']]
    assert contexto.empty is True


def test_auditoria_incluye_toda_geometria_y_rutas_existentes():
    """La lista no permite que rutas inexistentes oculten módulos del alcance."""
    assert all(ruta.is_file() for ruta in RUTAS_AUDITADAS)
    geometria = set((RAIZ / 'src/frontend/vistas/geometria').glob('*.py'))
    assert geometria <= set(RUTAS_AUDITADAS)


def test_cancelacion_absorbida_por_nicegui_no_muestra_error(monkeypatch):
    """El contrato io_bound que devuelve None al cancelar descarta el resultado."""
    async def comprobar():
        vista = _crear_vista_simulada(monkeypatch)
        iniciado = asyncio.Event()

        async def trabajador(*args):
            iniciado.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                return None

        monkeypatch.setattr(actualizacion.run, 'io_bound', trabajador)
        tarea = asyncio.create_task(vista._actualizar_figura())
        await iniciado.wait()
        tarea.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarea
        assert vista.ultimo_resultado is None
        vista._renderizar_error.assert_not_called()
        vista._renderizar_resumen.assert_not_called()
    asyncio.run(comprobar())


def test_exito_retira_marcado_de_error_anterior(monkeypatch):
    """Una corrección confirmada retira el marcado accesible y visual previo."""
    async def comprobar():
        vista = _crear_vista_simulada(monkeypatch)
        vista._ejecutar_js = MagicMock()
        monkeypatch.setattr(actualizacion, 'ejecutar_controlador_geometria', AsyncMock(return_value={'status': 'ERROR'}))
        await vista._actualizar_figura()
        vista._renderizar_error.assert_called_once()
        monkeypatch.setattr(actualizacion, 'ejecutar_controlador_geometria', AsyncMock(return_value={'status': 'OK', 'n': 2}))
        monkeypatch.setattr(vista, '_construir_figura', AsyncMock(return_value=True))
        await vista._actualizar_figura()
        vista._ejecutar_js.assert_called_with('window.scalaris?.geometria?.marcarInvalido(null);')
        assert vista.ultimo_resultado['status'] == 'OK'
    asyncio.run(comprobar())


def test_vaciado_retira_marcado_invalido(monkeypatch):
    """Una entrada vacía limpia las celdas previamente marcadas."""
    vista = _crear_vista_simulada(monkeypatch)
    vista._ejecutar_js = MagicMock()
    monkeypatch.setattr(vista, '_construir_carga', lambda: None)
    asyncio.run(vista._actualizar_figura())
    vista._ejecutar_js.assert_called_once_with('window.scalaris?.geometria?.marcarInvalido(null);')
