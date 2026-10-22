"""Herramientas, restauración y vigencia de la sesión real de Determinantes."""
import asyncio
from types import SimpleNamespace

import pytest
from nicegui import run, ui

from src.frontend.controladores.operaciones_matrices.vista_previa_determinante import preparar_presentacion_determinante
from src.frontend.controladores.operaciones_inversas.vista_previa import preparar_presentacion_previa
from src.frontend.vistas.mixin_sesion_matricial import MixinSesionMatricial
from tests.comun_construccion_vistas import construir_pagina


def test_presentadores_limitan_y_sanean():
    """Los dos presentadores limitan 50×50 y el determinante no agrega identidad."""
    for presentador in (preparar_presentacion_determinante, preparar_presentacion_previa):
        assert presentador([], 50)['estado'] == 'limite'
    formula = preparar_presentacion_determinante([['<script>']], 1)['bloques'][0][1]
    assert '<script>' not in formula and r'\color{gray}{?}' in formula
    assert '|A|' in formula and 'vmatrix' in formula and '\\mid I' not in formula


@pytest.mark.parametrize('valor,singular', [('2', False), ('0', True)])
def test_historial_restaura_sin_recalcular(monkeypatch, valor, singular):
    """Un éxito se guarda y restaura matriz y método retirando el contexto calculado."""
    async def comprobar(vista, cliente):
        """Calcula una matriz y restaura su registro tras editarla."""
        assert isinstance(vista, MixinSesionMatricial)
        assert {tab._props['name'] for tab in vista.pestanas_herramientas.descendants() if isinstance(tab, ui.tab)} == {
            'teclado', 'vista_previa', 'historial'}
        vista.panel_matriz.cargar_matriz([[valor]])
        vista.metodos_determinante.set_value('laplace')
        await vista.calcular(SimpleNamespace(sender=ui.button('Calcular')))
        assert vista.ultimo_resultado['es_singular'] == singular
        registro = vista.historial[0]
        assert registro['determinante'] == valor and registro['metodo'] == 'laplace'
        vista.panel_matriz.cargar_matriz([['9']])
        vista.metodos_determinante.set_value('lu')
        vista._restaurar_historial(registro)
        assert vista._capturar() == {'datos': [[valor]], 'dimension': 1, 'metodo': 'laplace'}
        assert vista.ultimo_resultado is None and vista.obtener_contexto_ia().resultado is None
        assert len(vista.historial) == 1
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


def test_error_no_se_registra(monkeypatch):
    """La captura inválida no entra en el historial de éxitos."""
    async def comprobar(vista, cliente):
        """Calcula una entrada inválida y comprueba el estado de sesión."""
        vista.panel_matriz.cargar_matriz([['1/0']])
        await vista.calcular(SimpleNamespace(sender=ui.button('Calcular')))
        assert not vista.historial and vista.ultimo_resultado is None
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


@pytest.mark.parametrize('accion', ['editar', 'metodo', 'restaurar', 'desmontar'])
def test_calculo_lento_no_publica_tras_cambiar_captura(monkeypatch, accion):
    """Una respuesta tardía nunca publica en una revisión posterior o cliente eliminado."""
    async def comprobar(vista, cliente):
        """Cambia la sesión dentro del trabajador antes de devolver su respuesta."""
        vista.panel_matriz.cargar_matriz([['2']])
        async def trabajador(funcion, captura):
            """Simula cada invalidación durante el trabajo matemático."""
            resultado = funcion(captura)
            if accion == 'editar':
                vista.panel_matriz.cargar_matriz([['3']])
            elif accion == 'metodo':
                vista.metodos_determinante.set_value('laplace')
            elif accion == 'restaurar':
                vista._restaurar_historial({'datos': [['2']], 'metodo': 'lu'})
            else:
                vista._desmontar_sesion()
            return resultado
        monkeypatch.setattr(run, 'io_bound', trabajador)
        await vista.calcular(SimpleNamespace(sender=ui.button('Calcular')))
        assert vista.ultimo_resultado is None and not vista.historial
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


def test_calculo_nuevo_gana_a_respuesta_anterior(monkeypatch):
    """La respuesta vieja no reemplaza el éxito ni retira la carga del nuevo cálculo."""
    async def comprobar(vista, cliente):
        """Publica un segundo cálculo antes de liberar la primera solicitud."""
        vista.panel_matriz.cargar_matriz([['2']])
        preparado, liberar = asyncio.Event(), asyncio.Event()
        async def trabajador(funcion, captura):
            """Retiene solo la primera captura, conservando el cálculo real."""
            if captura['datos'] == [['2']]:
                preparado.set()
                await liberar.wait()
            return funcion(captura)
        monkeypatch.setattr(run, 'io_bound', trabajador)
        boton = ui.button('Calcular')
        primera = asyncio.create_task(vista.calcular(SimpleNamespace(sender=boton)))
        await preparado.wait()
        vista.panel_matriz.cargar_matriz([['3']])
        await vista.calcular(SimpleNamespace(sender=boton))
        liberar.set()
        await primera
        assert str(vista.ultimo_resultado['determinante']) == '3'
        assert len(vista.historial) == 1 and vista.historial[0]['determinante'] == '3'
        assert boton._props['loading'] == 'false'
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))
