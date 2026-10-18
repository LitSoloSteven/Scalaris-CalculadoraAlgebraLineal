"""Preparación y controles compartidos de recuperación de figuras geométricas."""
from unittest.mock import AsyncMock, MagicMock
import asyncio
import json
import pytest

from nicegui import run, ui

from tests.comun import ejecutar_trabajador_simulado
from src.frontend.controladores.geometria.controlador_geometria import ControladorGeometria


def preparar_fallo_figura(monkeypatch, vista, carga):
    """Instala los mismos dobles del trabajador, figura, resumen y controles."""
    panel = MagicMock()
    vista.panel_ia = panel
    monkeypatch.setattr(vista, '_construir_carga', lambda: carga)
    monkeypatch.setattr(ui, 'run_javascript', lambda *argumentos, **opciones: None)
    monkeypatch.setattr(run, 'io_bound', ejecutar_trabajador_simulado)
    monkeypatch.setattr(vista, '_obtener_solo_figura', AsyncMock(return_value=None))
    resumen = MagicMock()
    monkeypatch.setattr(vista, '_renderizar_resumen', resumen)
    deslizador = MagicMock()
    monkeypatch.setattr(vista, '_construir_deslizador', deslizador)
    error = MagicMock()
    monkeypatch.setattr(vista, '_renderizar_error', error)
    return panel, resumen, deslizador, error


async def comprobar_recuperacion_figura(vista, dobles):
    """Exige limpiar datos obsoletos, presentar un error y refrescar el contexto."""
    panel, resumen, deslizador, error = dobles
    await vista._actualizar_figura()
    assert vista.ultimo_resultado is None
    assert vista.ultimo_hash_entrada is None
    assert vista._clave_figura is None
    assert vista._elemento_plotly is None
    assert vista._primer_dibujo is True
    resumen.assert_not_called()
    deslizador.assert_not_called()
    error.assert_called_once()
    panel.programar_actualizacion_contexto.assert_called_once()


def comprobar_rectas_incompatibles(carga):
    """Procesa la misma captura y exige éxito de análisis con sistema incompatible."""
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado['estado'] == 'EXITO'
    assert resultado['estado_solucion'] == 'SIN_SOLUCION'
    return resultado


def comprobar_error_longitud(carga, procesar):
    """Conserva estado, mensaje y coordenada del error de longitud de una celda."""
    resultado = procesar(json.dumps(carga))
    assert resultado['estado'] == 'ERROR'
    assert resultado.get('codigo') is None
    assert 'longitud máxima permitida' in resultado['mensaje']
    assert resultado['celda_error'] is not None
    return resultado


async def cancelar_figura_pendiente(vista, iniciado):
    """Cancela después de iniciar el trabajo y exige propagación sin resultado parcial."""
    tarea = asyncio.create_task(vista._actualizar_figura())
    await iniciado.wait()
    tarea.cancel()
    with pytest.raises(asyncio.CancelledError):
        await tarea
    assert vista.ultimo_resultado is None
