"""Antirrebote compartido y descarte de recomendaciones obsoletas."""
import asyncio
from unittest.mock import Mock

import pytest
from nicegui import run
from src.frontend.vistas.operaciones_matrices import recomendacion_determinante
from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante
from tests.comun_construccion_vistas import construir_pagina


def test_ediciones_agrupadas_y_redimensionado_recomiendan_una_vez(monkeypatch):
    """Varias ediciones reemplazan la espera y solo procesan la captura final."""
    async def comprobar(vista, cliente):
        """Edita celdas sin esperar y comprueba que el último tamaño llega al controlador."""
        recomendar = Mock(wraps=ControladorDeterminante.recomendar_captura)
        monkeypatch.setattr(ControladorDeterminante, 'recomendar_captura', recomendar)
        vista.panel_matriz.celdas[0][0].set_value('1')
        anterior = vista.recomendacion.tarea
        vista.panel_matriz.celdas[0][0].set_value('2')
        vista.panel_matriz.cargar_matriz([['3', '0'], ['0', '1']])
        await asyncio.gather(anterior, vista.recomendacion.tarea, return_exceptions=True)
        assert anterior.cancelled() and recomendar.call_count == 1
        captura = recomendar.call_args.args[0]
        assert captura['dimension'] == 2 and captura['datos'][0][0] == '3'
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


def test_respuesta_antigua_que_absorbe_cancelacion_no_reemplaza_la_actual(monkeypatch):
    """Una respuesta tardía del trabajador nunca sustituye la recomendación vigente."""
    async def comprobar(vista, cliente):
        """Publica la captura nueva antes de liberar un trabajador viejo cancelado."""
        monkeypatch.setattr(recomendacion_determinante, 'ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS', 0)
        preparado, liberar = asyncio.Event(), asyncio.Event()
        async def trabajador(funcion, captura):
            """Reproduce un transporte que absorbe CancelledError durante el trabajo."""
            if captura['datos'][0][0] == '1':
                preparado.set()
                try:
                    await liberar.wait()
                except asyncio.CancelledError:
                    await liberar.wait()
                return {'estado': 'ERROR', 'mensaje': 'Respuesta antigua'}
            return funcion(captura)
        monkeypatch.setattr(run, 'io_bound', trabajador)
        vista.panel_matriz.celdas[0][0].set_value('1')
        anterior = vista.recomendacion.tarea
        await preparado.wait()
        vista.panel_matriz.celdas[0][0].set_value('2')
        await vista.recomendacion.tarea
        liberar.set()
        await anterior
        assert vista.recomendacion.respuesta['estado'] == 'EXITO'
        assert vista.recomendacion.contenedor._props['role'] == 'status'
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


@pytest.mark.parametrize('desmontar', [False, True])
def test_limpiar_o_desmontar_cancela_espera(monkeypatch, desmontar):
    """Limpiar o abandonar la vista retira la tarea antes de llamar al controlador."""
    async def comprobar(vista, cliente):
        """Cancela una espera pendiente y no permite publicar una recomendación vieja."""
        recomendar = Mock()
        monkeypatch.setattr(ControladorDeterminante, 'recomendar_captura', recomendar)
        vista.panel_matriz.celdas[0][0].set_value('1')
        tarea = vista.recomendacion.tarea
        vista._desmontar_sesion() if desmontar else vista.limpiar_todo()
        await asyncio.wait_for(asyncio.gather(tarea, return_exceptions=True), timeout=2)
        assert tarea.cancelled() and vista.recomendacion.tarea is None
        assert vista.recomendacion.respuesta is None
        recomendar.assert_not_called()
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))
