"""Pruebas del contexto de cliente en tareas y llamadas JavaScript de NiceGUI."""
import asyncio
from pathlib import Path
import re
from tests.comun import comprobar_tarea_en_cliente
from tests.comun_clientes import ClienteSimulado
from src.frontend.vistas.geometria.vista_geometria import VistaGeometria
from src.frontend.componentes.glosa_panel_lateral import PanelLateralGlosaMixin


def test_geometria_ejecuta_js_desde_cliente():
    """Las vistas geométricas evitan el contexto global de ejecución JavaScript."""
    ruta_vista = Path('src/frontend/vistas/geometria/vista_geometria.py')
    ruta_escenas = Path('src/frontend/vistas/geometria/mixin_escenas.py')
    assert ruta_vista.exists()
    assert ruta_escenas.exists()
    contenido_vista = ruta_vista.read_text(encoding='utf-8')
    contenido_escenas = ruta_escenas.read_text(encoding='utf-8')
    assert 'ui.run_javascript(' not in contenido_vista
    assert 'ui.run_javascript(' not in contenido_escenas


def test_contrato_cliente_vista_geometria():
    """La vista posee cliente, ejecución JavaScript y lanzamiento contextual de tareas."""
    contenido = Path('src/frontend/vistas/geometria/vista_geometria.py').read_text(encoding='utf-8')
    assert 'self._cliente = ' in contenido
    assert 'def _ejecutar_javascript(self' in contenido
    assert 'def _lanzar_tarea(self' in contenido
    assert 'self._lanzar_tarea(self._actualizar_con_antirrebote())' in contenido


def test_contrato_tareas_glosa_panel_lateral():
    """Glosa lanza sus envíos mediante el protocolo de cliente."""
    ruta = Path('src/frontend/componentes/glosa_panel_lateral.py')
    assert ruta.exists()
    contenido = ruta.read_text(encoding='utf-8')
    assert 'asyncio.create_task(self._enviar_consulta' not in contenido
    assert 'def _lanzar_tarea(self' in contenido
    assert 'self._lanzar_tarea(self._enviar_consulta' in contenido


def test_contrato_renderizar_error_geometria():
    """El renderizado de errores ejecuta JavaScript exclusivamente desde el cliente."""
    contenido = Path('src/frontend/vistas/geometria/vista_geometria.py').read_text(encoding='utf-8')
    coincidencia = re.search(r'def _renderizar_error\(self.*?\n(?=\s{4}def |\Z)', contenido, re.DOTALL)
    assert coincidencia is not None
    cuerpo = coincidencia.group(0)
    assert 'ui.run_javascript' not in cuerpo
    assert 'self._ejecutar_javascript' in cuerpo


def test_tarea_y_js_vista_geometria_con_cliente_simulado():
    """Geometría respeta el estado del cliente y entra en su contexto asíncrono."""
    async def comprobar():
        """Comprueba los datos y el estado del escenario de la prueba."""
        vista = VistaGeometria()
        cliente = ClienteSimulado()
        vista._cliente = cliente
        vista._ejecutar_javascript("console.log('hola');")
        assert cliente.llamadas_js == ["console.log('hola');"]
        cliente.is_deleted = True
        vista._ejecutar_javascript("console.log('ignorado');")
        assert len(cliente.llamadas_js) == 1
        cliente.is_deleted = False
        await comprobar_tarea_en_cliente(vista._lanzar_tarea, cliente, 'ok')
    asyncio.run(comprobar())


class PanelLateralSimulado(PanelLateralGlosaMixin):
    """Dock mínimo para comprobar el protocolo del cliente."""

    def __init__(self):
        self._cliente = None


def test_tarea_y_desplazamiento_glosa_con_cliente_simulado():
    """Glosa desplaza la bitácora y ejecuta las tareas dentro del cliente."""
    async def comprobar():
        """Comprueba los datos y el estado del escenario de la prueba."""
        panel_lateral = PanelLateralSimulado()
        cliente = ClienteSimulado()
        panel_lateral._cliente = cliente
        panel_lateral._desplazar_al_final()
        assert len(cliente.llamadas_js) == 1
        assert 'glosa-bitacora' in cliente.llamadas_js[0]
        await comprobar_tarea_en_cliente(panel_lateral._lanzar_tarea, cliente, 42)
    asyncio.run(comprobar())
