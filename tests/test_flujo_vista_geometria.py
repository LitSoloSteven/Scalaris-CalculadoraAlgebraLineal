"""Pruebas de confirmación y recuperación de figuras geométricas."""
import asyncio
from unittest.mock import MagicMock, AsyncMock
from nicegui import ui, run
from src.frontend.vistas.geometria.vista_geometria import VistaGeometria
from tests.comun import ejecutar_trabajador_simulado


def test_actualizar_figura_inicial_fallida(monkeypatch):
    """Una figura inicial fallida no confirma ni expone resultados parciales."""
    async def _test():
        vista = VistaGeometria()
        vista.escena = 'rectas-planos'
        panel_ia_simulado = MagicMock()
        vista.panel_ia = panel_ia_simulado
        monkeypatch.setattr(vista, '_construir_carga', lambda: {'matrix_A': [['1', '0'], ['0', '1']], 'vector_b': ['1', '2']})
        monkeypatch.setattr(ui, 'run_javascript', lambda *args, **kwargs: None)

        monkeypatch.setattr(run, 'io_bound', ejecutar_trabajador_simulado)
        monkeypatch.setattr(vista, '_obtener_solo_figura', AsyncMock(return_value=None))
        resumen_simulado = MagicMock()
        monkeypatch.setattr(vista, '_renderizar_resumen', resumen_simulado)
        deslizador_simulado = MagicMock()
        monkeypatch.setattr(vista, '_construir_deslizador', deslizador_simulado)
        error_simulado = MagicMock()
        monkeypatch.setattr(vista, '_renderizar_error', error_simulado)
        await vista._actualizar_figura()
        assert vista.ultimo_resultado is None
        assert vista.ultimo_hash_entrada is None
        assert vista._clave_figura is None
        assert vista._elemento_plotly is None
        assert vista._primer_dibujo is True
        resumen_simulado.assert_not_called()
        deslizador_simulado.assert_not_called()
        error_simulado.assert_called_once()
        panel_ia_simulado.programar_actualizacion_contexto.assert_called_once()

    asyncio.run(_test())


def test_actualizar_figura_reutilizada_fallida(monkeypatch):
    """Una figura reutilizada fallida permite reiniciar el dibujo sin datos obsoletos."""
    async def _test():
        vista = VistaGeometria()
        vista.escena = 'rectas-planos'
        vista._primer_dibujo = False
        grafica_simulada = MagicMock()
        vista._elemento_plotly = grafica_simulada
        vista._clave_figura = ('rectas-planos', 2)
        vista.ultimo_hash_entrada = 9999
        vista.ultimo_resultado = {'status': 'SUCCESS', 'n': 2}
        panel_ia_simulado = MagicMock()
        vista.panel_ia = panel_ia_simulado
        monkeypatch.setattr(vista, '_construir_carga', lambda: {'matrix_A': [['2', '0'], ['0', '2']], 'vector_b': ['2', '4']})
        monkeypatch.setattr(ui, 'run_javascript', lambda *args, **kwargs: None)

        monkeypatch.setattr(run, 'io_bound', ejecutar_trabajador_simulado)
        monkeypatch.setattr(vista, '_obtener_solo_figura', AsyncMock(return_value=None))
        resumen_simulado = MagicMock()
        monkeypatch.setattr(vista, '_renderizar_resumen', resumen_simulado)
        deslizador_simulado = MagicMock()
        monkeypatch.setattr(vista, '_construir_deslizador', deslizador_simulado)
        error_simulado = MagicMock()
        monkeypatch.setattr(vista, '_renderizar_error', error_simulado)
        await vista._actualizar_figura()
        assert vista.ultimo_resultado is None
        assert vista.ultimo_hash_entrada is None
        assert vista._clave_figura is None
        assert vista._elemento_plotly is None
        assert vista._primer_dibujo is True
        resumen_simulado.assert_not_called()
        deslizador_simulado.assert_not_called()
        error_simulado.assert_called_once()
        panel_ia_simulado.programar_actualizacion_contexto.assert_called_once()

    asyncio.run(_test())


def test_construir_figura_devuelve_booleano(monkeypatch):
    """La construcción distingue fracaso y éxito mediante su retorno booleano."""
    async def _test():
        vista = VistaGeometria()
        vista.contenedor_figura = MagicMock()
        monkeypatch.setattr(vista, '_obtener_solo_figura', AsyncMock(return_value=None))
        monkeypatch.setattr(ui, 'run_javascript', lambda *args, **kwargs: None)
        error_simulado = MagicMock()
        monkeypatch.setattr(vista, '_renderizar_error', error_simulado)
        resultado = await vista._construir_figura({}, 'rectas-planos')
        assert resultado is False
        error_simulado.assert_called_once()
        figura_simulada = MagicMock()
        monkeypatch.setattr(vista, '_obtener_solo_figura', AsyncMock(return_value=figura_simulada))
        monkeypatch.setattr(ui, 'plotly', lambda figura: MagicMock())
        monkeypatch.setattr(ui, 'element', lambda *args, **kwargs: MagicMock())
        resultado_segundo = await vista._construir_figura({}, 'rectas-planos')
        assert resultado_segundo is True

    asyncio.run(_test())
