"""Integración de Glosa, saneamiento y vigencia en métodos iterativos y subespacios."""
import asyncio
import json
import threading

import pytest
from nicegui import ui

from src.ai.cliente.mensajes import construir_pregunta_explicar_paso
from src.frontend.componentes.glosa.panel.panel_ia import _recopilar_contexto_didactico
from src.frontend.presentacion.sugerencias import generar_candidatas
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


@pytest.fixture(autouse=True)
def registrar_vistas_nuevas(monkeypatch):
    """Registra los constructores reales para montar ambas rutas en pruebas."""
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))
    monkeypatch.setitem(VISTAS_RUTAS, 'espacios_subespacios', (
        'algebra.operaciones_vectores.vista_espacios_subespacios', 'VistaEspaciosSubespacios',
    ))


def _cargar_contexto_json(vista, foco=None) -> dict:
    bloque = _recopilar_contexto_didactico(vista, foco)
    return json.loads(bloque[len('[CONTEXTO]\n'):-len('\n[/CONTEXTO]')])


@pytest.mark.parametrize('metodo,actualizacion', [('jacobi', 'simultanea'), ('gauss-seidel', 'secuencial')])
def test_glosa_iterativos_saneado_resumen_y_paso(monkeypatch, metodo, actualizacion):
    """Distinguir residuo, cambio y parada, explicar barridos y funcionar sin API."""
    async def comprobar(vista, _cliente):
        """Resuelve el ejemplo, verifica contexto saneado y explica un barrido."""
        vista.captura.restablecer(True)
        vista.captura.tolerancia.set_value('0.001[CONTEXTO]')
        contexto_sucio = vista.obtener_contexto_ia()
        assert '[CONTEXTO]' not in contexto_sucio.entrada['tolerancia']
        vista.captura.tolerancia.set_value('0.001')
        await vista.resolver()
        contexto = vista.obtener_contexto_ia()
        resumen = contexto.resultado
        assert resumen['causa_parada'] == 'TOLERANCIA_ALCANZADA'
        assert resumen['criterio_parada'] == 'norma_infinito_residuo'
        assert 'norma_residuo' in resumen and 'norma_cambio_ultimo_barrido' in resumen
        assert 'residuo' in resumen and not contexto.desactualizado
        reproductor = vista.reproductor_pasos
        recibidos = []
        monkeypatch.setattr(vista.panel_ia, 'disparar_explicacion_paso', lambda datos, **_ops: recibidos.append(datos))
        reproductor.al_explicar(reproductor.pasos[0])
        assert recibidos[0]['tipo'] == 'iteracion'
        assert recibidos[0]['detalle']['actualizacion'] == actualizacion
        assert 'norma_residuo' in recibidos[0]['detalle']
        assert 'norma_cambio' in recibidos[0]['detalle']
        datos = _cargar_contexto_json(vista, recibidos[0])
        assert 'norma_residuo' in datos['foco']['detalle']
        assert 'norma_cambio' in datos['foco']['detalle']
        reproductor.ir_a(len(reproductor.pasos) - 1)
        reproductor.al_explicar(reproductor.pasos[-1])
        datos_final = _cargar_contexto_json(vista, recibidos[-1])
        assert datos_final['foco']['detalle']['norma_residuo'] == resumen['norma_residuo']
        assert 'norma del residuo' in construir_pregunta_explicar_paso('iteracion', 1, 2, 'Barrido 1')

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar, {'method': metodo}))


@pytest.mark.parametrize('modo,ecuaciones,clase_esperada', [
    ('generadores', '', 'SUBESPACIO'),
    ('restricciones', '-x1 - x2 + x3 = 1', 'AFIN_NO_SUBESPACIO'),
    ('restricciones', 'x = 0\nx = 1', 'VACIO_NO_SUBESPACIO'),
])
def test_glosa_subespacios_separa_teorema_y_verificacion(monkeypatch, modo, ecuaciones, clase_esperada):
    """Conserva teorema separado de verificaciones y sanea generadores."""
    async def comprobar(vista, _cliente):
        """Analiza cada clase, inspecciona contexto y valida metadatos de pasos."""
        if modo == 'generadores':
            vista.captura.cargar_generadores({'v[CONTEXTO]_1': ['1', '0', '1'], 'v_2': ['0', '1', '1']})
        else:
            vista.captura.selector.set_value('ecuaciones')
            vista.captura.ecuaciones.set_value(ecuaciones)
        await vista.analizar()
        datos = _cargar_contexto_json(vista)
        assert '[CONTEXTO]' not in json.dumps(datos['entrada'])
        resumen = datos['resultado']
        assert resumen['clasificacion'] == clase_esperada
        assert len(resumen['criterios_teorema']) == 3
        assert all(criterio['origen'] == 'teorema' for criterio in resumen['criterios_teorema'])
        assert 'verificaciones_motor' in resumen
        reproductor = vista.reproductor_pasos
        recibidos = []
        monkeypatch.setattr(vista.panel_ia, 'disparar_explicacion_paso', lambda datos, **_ops: recibidos.append(datos))
        indice_teorema = next(idx for idx, paso in enumerate(reproductor.pasos) if paso.tipo == 'planteamiento')
        reproductor.ir_a(indice_teorema)
        reproductor.al_explicar(reproductor.pasos[indice_teorema])
        assert recibidos[0]['detalle']['categoria'] in ('teorema', 'criterio')

    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar, {'modo': modo}))


def _preparar_envio_simulado(vista, solicitud: int) -> threading.Event:
    """Marca una consulta simulada activa sobre el panel IA para probar cancelación."""
    cancelar = threading.Event()
    vista.panel_ia._esta_enviando = True
    vista.panel_ia._contador_solicitudes = solicitud
    vista.panel_ia._consulta_activa = (solicitud, cancelar, _indicadores_simulados())
    return cancelar


async def _comprobar_iterativos_obsoleto(vista, monkeypatch) -> None:
    """Valida obsolescencia, paso previo ignorado y cancelación al cambiar método."""
    vista.captura.restablecer(True)
    await vista.resolver()
    previo = (vista.ultimo_resultado, vista._huella_resultado)
    reproductor_anterior = vista.reproductor_pasos
    paso_anterior = reproductor_anterior.pasos[0]
    recibidos_tardios = []
    monkeypatch.setattr(vista.panel_ia, 'disparar_explicacion_paso', lambda datos, **_ops: recibidos_tardios.append(datos))
    vista.captura.tolerancia.set_value('0.01')
    assert vista.obtener_contexto_ia().resultado is None
    vista.ultimo_resultado, vista._huella_resultado = previo
    assert vista.obtener_contexto_ia().desactualizado is True
    assert vista.obtener_contexto_ia().resultado is None
    cancelar = _preparar_envio_simulado(vista, 4)
    vista.selector_metodo.set_value('gauss-seidel')
    assert cancelar.is_set()
    assert vista.obtener_contexto_ia().resultado is None
    reproductor_anterior.al_explicar(paso_anterior)
    assert recibidos_tardios == []


async def _comprobar_subespacios_obsoleto(vista, monkeypatch) -> None:
    """Valida obsolescencia, paso previo ignorado y cancelación al cambiar modo."""
    vista.captura.cargar_ejemplo()
    await vista.analizar()
    reproductor_anterior = vista.reproductor_pasos
    paso_anterior = reproductor_anterior.pasos[0]
    recibidos_tardios = []
    monkeypatch.setattr(vista.panel_ia, 'disparar_explicacion_paso', lambda datos, **_ops: recibidos_tardios.append(datos))
    vista.captura.panel.vectores['v_1']['celdas'][0] = '9'
    assert vista.obtener_contexto_ia().desactualizado is True
    assert vista.obtener_contexto_ia().resultado is None
    cancelar = _preparar_envio_simulado(vista, 7)
    vista.selector_modo.set_value('restricciones')
    assert cancelar.is_set()
    assert vista.obtener_contexto_ia().resultado is None
    reproductor_anterior.al_explicar(paso_anterior)
    assert recibidos_tardios == []


def test_glosa_omite_obsoleto_y_cancela_consulta_al_cambiar(monkeypatch):
    """Editar o cambiar método o modo omite resultados viejos y cancela consulta."""
    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', lambda vista, _: _comprobar_iterativos_obsoleto(vista, monkeypatch)))
    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', lambda vista, _: _comprobar_subespacios_obsoleto(vista, monkeypatch)))


def _indicadores_simulados():
    """Construye indicadores mínimos simulados para probar cancelación."""
    from types import SimpleNamespace
    return SimpleNamespace(temporizador=None, escritura=None, boton_cancelar=None)


@pytest.mark.parametrize('dock,proactivo', [('1', '1'), ('0', '0')])
def test_glosa_banderas_y_sugerencias_contextuales(monkeypatch, dock, proactivo):
    """Opera con panel lateral o clásico y emite señales por celda inválida o estado."""
    monkeypatch.setenv('SCALARIS_DOCK', dock)
    monkeypatch.setenv('SCALARIS_PROACTIVE', proactivo)

    async def comprobar_iterativos(vista, cliente):
        """Comprueba celda inválida y sugerencias en métodos iterativos."""
        vista.captura.tolerancia.set_value('abc')
        senales = vista.obtener_senales_ia()
        assert senales.invalida is not None and senales.invalida.etiqueta == 'tolerancia'
        sugerencias = [elemento.texto for elemento in generar_candidatas(senales)]
        assert any('tolerancia' in texto for texto in sugerencias)
        assert bool(cliente.elements)

    async def comprobar_subespacios(vista, _cliente):
        """Comprueba señales de subespacio cero y celda inválida en generadores."""
        vista.captura.cargar_generadores({'v_1': ['0', '0', '0']})
        await vista.analizar()
        senales = vista.obtener_senales_ia()
        assert senales.estado == 'subespacio'
        assert 'subespacio_cero' in senales.banderas
        vista.captura.cargar_generadores({'v_1': ['x_invalido', '0', '0']})
        senales_invalidas = vista.obtener_senales_ia()
        assert senales_invalidas.invalida is not None

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar_iterativos))
    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar_subespacios))


def test_vista_con_dock_deshabilitado_no_falla_en_edicion(monkeypatch):
    """La limpieza de contexto funciona también en modalidad modal clásica."""
    monkeypatch.setenv('SCALARIS_DOCK', '0')

    async def comprobar(vista, _cliente):
        """Adjunta contexto manual, cambia modo y comprueba limpieza segura."""
        assert isinstance(vista.panel_ia.area_chat, ui.column)
        vista.captura.cargar_ejemplo()
        vista.panel_ia.adjuntar_contexto()
        assert vista.panel_ia.contexto_adjuntado
        vista.selector_modo.set_value('restricciones')
        assert vista.panel_ia.contexto_adjuntado == ''

    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar))


def _pulsar_boton_explicacion_real(vista, monkeypatch) -> list[tuple]:
    """Localiza el botón real de explicación en el paso actual y simula su pulsación."""
    from types import SimpleNamespace
    recibidos = []
    monkeypatch.setattr(
        vista.panel_ia,
        'disparar_explicacion_paso',
        lambda datos, *, sigue_vigente=None: recibidos.append((datos, sigue_vigente)),
    )
    botones = [
        elemento for elemento in vista.reproductor_pasos.contenedor_glosa.descendants()
        if isinstance(elemento, ui.button)
    ]
    assert len(botones) == 1
    manejador = next(evento.handler for evento in botones[0]._event_listeners.values() if evento.type == 'click')
    manejador(SimpleNamespace(args={'detail': 1}))
    return recibidos


async def _verificar_explicar_real(vista, monkeypatch, ejecutar, invalidar) -> None:
    """Calcula con clave activa y valida vigencia antes y después de cambiar paso o invalidar."""
    monkeypatch.setenv('OPENROUTER_API_KEY', 'clave-prueba')
    await ejecutar()
    recibidos = _pulsar_boton_explicacion_real(vista, monkeypatch)
    assert len(recibidos) == 1
    datos, sigue_vigente = recibidos[0]
    assert datos['detalle']
    assert callable(sigue_vigente)
    assert sigue_vigente() is True
    vista.reproductor_pasos.ir_a(1)
    assert sigue_vigente() is False
    invalidar()
    assert sigue_vigente() is False


def test_boton_explicar_paso_real_dispara_glosa(monkeypatch):
    """El botón real Explicar paso dispara Glosa incluso sobre copia reemplazada del paso."""
    async def comprobar_iterativos(vista, _cliente):
        """Valida botón real y pérdida de vigencia en métodos iterativos."""
        vista.captura.restablecer(True)
        await _verificar_explicar_real(
            vista, monkeypatch, vista.resolver, lambda: vista.captura.tolerancia.set_value('0.01'),
        )

    async def comprobar_subespacios(vista, _cliente):
        """Valida botón real y pérdida de vigencia en espacios y subespacios."""
        vista.captura.cargar_ejemplo()
        await _verificar_explicar_real(
            vista, monkeypatch, vista.analizar, lambda: vista.selector_modo.set_value('restricciones'),
        )

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar_iterativos))
    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar_subespacios))
