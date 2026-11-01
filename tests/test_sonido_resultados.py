"""Señales tras acciones efectivas, sin duplicados ni resultados obsoletos."""
import asyncio
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.ai.respuestas import ResultadoIA, TipoErrorIA
from src.frontend.componentes import glosa_envio, limpieza_captura
from src.frontend.componentes.exportacion_pdf import boton as pdf


@pytest.mark.parametrize('vacia,fallo_movimiento', [(False, False), (False, True), (True, False)])
def test_limpieza_emite_despues_del_vaciado_efectivo(monkeypatch, vacia, fallo_movimiento):
    """La ausencia de animación no impide la señal; vaciar sin datos permanece silencioso."""
    eventos = []
    captura = SimpleNamespace(esta_completamente_vacio=lambda: vacia,
                              limpiar_todo=lambda: eventos.append('vaciar'))
    control = limpieza_captura.LimpiezaCaptura(captura, lambda: True)
    control._animar_captura = AsyncMock(side_effect=TimeoutError() if fallo_movimiento else None)
    control._finalizar_movimiento = AsyncMock()
    monkeypatch.setattr(limpieza_captura, 'emitir_sonido', lambda nombre: eventos.append(nombre))
    asyncio.run(control.ejecutar())
    assert eventos == (['vaciar'] if vacia else ['vaciar', 'limpiar'])
    assert control._limpiando is False


def test_limpieza_desmontada_o_fallida_no_emite(monkeypatch):
    """No se anuncia una limpieza que no ha llegado a ejecutarse."""
    emision = Mock()
    captura = SimpleNamespace(esta_completamente_vacio=lambda: False,
                              limpiar_todo=Mock(side_effect=ValueError('Fallo simulado')))
    control = limpieza_captura.LimpiezaCaptura(captura, lambda: False)
    control._animar_captura = AsyncMock()
    control._finalizar_movimiento = AsyncMock()
    monkeypatch.setattr(limpieza_captura, 'emitir_sonido', emision)
    asyncio.run(control.ejecutar())
    captura.limpiar_todo.assert_not_called()
    control.sigue_montada = lambda: True
    with pytest.raises(ValueError):
        asyncio.run(control.ejecutar())
    emision.assert_not_called()
    assert control._limpiando is False


@pytest.mark.parametrize('vigente,fallo', [(True, False), (False, False), (True, True)])
def test_pdf_solo_suena_al_entregar_documento_vigente(monkeypatch, vigente, fallo):
    """La señal sigue a la descarga, sin emitirse tras captura fallida o resultado obsoleto."""
    eventos = []
    control = pdf.ExportacionPDF.__new__(pdf.ExportacionPDF)
    control.enlace = SimpleNamespace(raiz='captura')
    control.resultado = {}
    control.herramienta = 'sistemas'
    control.dialogo = SimpleNamespace(estado=SimpleNamespace(set_text=Mock()))
    control._pausar_procedimiento = Mock()
    control._puede_entregar = Mock(side_effect=[True, vigente])
    control._dialogo_abierto = Mock(return_value=True)
    monkeypatch.setattr(pdf, 'capturar_regiones', AsyncMock(return_value=[], side_effect=ValueError() if fallo else None))
    monkeypatch.setattr(pdf.run, 'io_bound', AsyncMock(return_value=(b'%PDF', False)))
    monkeypatch.setattr(pdf.ui, 'download', lambda *datos, **opciones: eventos.append('descargar'))
    monkeypatch.setattr(pdf, 'emitir_sonido', lambda nombre: eventos.append(nombre))
    asyncio.run(control._exportar({'fecha': '2026-10-31'}, ()))
    assert eventos == (['exportar_inicio', 'descargar', 'exportar'] if vigente and not fallo else ['exportar_inicio'])


@pytest.mark.parametrize('exito', [True, False])
def test_glosa_distingue_respuesta_de_error(monkeypatch, exito):
    """Glosa emite exactamente una señal después de presentar su respuesta."""
    emision = Mock()
    instancia = SimpleNamespace(historial_chat=[], area_chat=nullcontext(),
                                _renderizar_mensaje=Mock(), _desplazar_al_final=Mock())
    monkeypatch.setattr(glosa_envio.banderas, 'panel_lateral_habilitado', lambda: False)
    monkeypatch.setattr(glosa_envio, 'emitir_sonido', emision)
    resultado = ResultadoIA(exito, 'Texto de prueba', None if exito else TipoErrorIA.SERVICIO)
    glosa_envio.EnvioGlosaMixin._procesar_resultado(instancia, resultado)
    emision.assert_called_once_with('respuesta' if exito else 'error')
    instancia._renderizar_mensaje.assert_called_once()
