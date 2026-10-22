"""Descarte de respuestas obsoletas y ejecución de controladores en trabajador."""
import asyncio
import json
import threading
from types import SimpleNamespace
import pytest
from nicegui import run, ui
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from tests.comun_construccion_vistas import construir_pagina


def test_trabajador_real_no_ejecuta_el_controlador_en_el_hilo_del_bucle():
    """El controlador recibe una copia y devuelve el mismo dato desde otro hilo."""
    async def _comprobar():
        hilo = threading.get_ident()
        vista = SimpleNamespace(contenedor_resultados=SimpleNamespace(is_deleted=False))
        captura = {'datos': [['1/3']]}
        respuesta, huella = await ejecutar_calculo_vigente(
            vista, lambda: {'datos': [fila[:] for fila in captura['datos']]},
            lambda datos: (threading.get_ident(), datos))
        assert respuesta[0] != hilo
        assert respuesta[1] == captura and respuesta[1] is not captura
        assert len(huella) == 40
    asyncio.run(_comprobar())


def test_cancelacion_del_trabajador_real_se_propaga():
    """La cancelación del trabajador real se propaga en lugar de devolver None."""
    async def _comprobar():
        inicio, terminar = threading.Event(), threading.Event()
        vista = SimpleNamespace(contenedor_resultados=SimpleNamespace(is_deleted=False))
        def _trabajar(datos):
            inicio.set()
            terminar.wait(3)
            return datos
        tarea = asyncio.create_task(ejecutar_calculo_vigente(vista, lambda: {}, _trabajar))
        try:
            assert await asyncio.to_thread(inicio.wait, 2)
            tarea.cancel()
            with pytest.raises(asyncio.CancelledError):
                await tarea
        finally:
            terminar.set()
    asyncio.run(_comprobar())


@pytest.mark.parametrize('cambio', ['huella', 'revision', 'contenedor', 'eliminado', 'sin_respuesta'])
def test_guarda_rechaza_todos_los_origenes_obsoletos(monkeypatch, cambio):
    """Captura distinta, revisión, navegación y cancelación no publican respuestas."""
    async def _comprobar():
        datos = {'valor': '1'}
        vista = SimpleNamespace(_revision_captura=1, contenedor_resultados=SimpleNamespace(is_deleted=False))
        async def _trabajar(calcular, captura):
            if cambio == 'huella': datos['valor'] = '2'
            if cambio == 'revision': vista._revision_captura += 1
            if cambio == 'contenedor': vista.contenedor_resultados = SimpleNamespace(is_deleted=False)
            if cambio == 'eliminado': vista.contenedor_resultados.is_deleted = True
            return None if cambio == 'sin_respuesta' else calcular(captura)
        monkeypatch.setattr(run, 'io_bound', _trabajar)
        assert await ejecutar_calculo_vigente(vista, lambda: dict(datos), lambda captura: captura) is None
    asyncio.run(_comprobar())


@pytest.mark.parametrize('obsoleto', [False, True])
def test_error_del_trabajador_solo_se_propaga_si_es_vigente(monkeypatch, obsoleto):
    """Un fallo antiguo no sustituye los estados de una captura nueva."""
    async def _comprobar():
        vista = SimpleNamespace(_revision_captura=1, contenedor_resultados=SimpleNamespace(is_deleted=False))
        async def _fallar(*argumentos):
            if obsoleto: vista._revision_captura += 1
            raise ValueError('fallo simulado')
        monkeypatch.setattr(run, 'io_bound', _fallar)
        if obsoleto:
            assert await ejecutar_calculo_vigente(vista, lambda: {}, lambda datos: datos) is None
        else:
            with pytest.raises(ValueError, match='fallo simulado'):
                await ejecutar_calculo_vigente(vista, lambda: {}, lambda datos: datos)
    asyncio.run(_comprobar())


def _nucleo(vista, herramienta):
    if herramienta == 'matrices':
        vista.entrada_expresion.set_value('A+A')
        return vista._evaluar_nucleo(ui.button('prueba'), 'A+A')
    return vista._calcular_nucleo() if herramienta == 'leontief' else vista._analizar_nucleo()


def _editar_y_restaurar(vista, herramienta):
    campo = (vista.panel_captura_matrices.matrices['A']['entradas'][0][0]
             if herramienta == 'matrices' else vista.entradas_coeficientes[0][0])
    valor = campo.value
    campo.set_value('7/13')
    campo.set_value(valor)


@pytest.mark.parametrize('herramienta', ['matrices', 'leontief', 'transformaciones'])
def test_vistas_descartan_edicion_y_restauracion_durante_calculo(monkeypatch, herramienta):
    """Restaurar el mismo texto no revive una respuesta de una revisión anterior."""
    async def _comprobar(vista, cliente):
        async def _trabajar(*argumentos):
            _editar_y_restaurar(vista, herramienta)
            await asyncio.sleep(0)
            return json.dumps({'estado': 'EXITO'})
        monkeypatch.setattr(run, 'io_bound', _trabajar)
        await _nucleo(vista, herramienta)
        assert vista.ultimo_resultado is None
        assert not getattr(vista, '_huella_resultado', None)
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))


@pytest.mark.parametrize('herramienta', ['leontief', 'transformaciones'])
def test_reconstruir_controles_descarta_captura_aunque_el_texto_coincida(monkeypatch, herramienta):
    """Las identidades de controles detectan una reconstrucción durante el trabajador."""
    async def _comprobar(vista, cliente):
        async def _trabajar(*argumentos):
            vista._generar_cuadricula()
            return json.dumps({'estado': 'EXITO'})
        monkeypatch.setattr(run, 'io_bound', _trabajar)
        await _nucleo(vista, herramienta)
        assert vista.ultimo_resultado is None
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))


@pytest.mark.parametrize('herramienta', ['leontief', 'transformaciones'])
def test_editar_en_el_primer_yield_no_deja_estado_de_carga(monkeypatch, herramienta):
    """Una edición antes del núcleo retira el indicador y conserva el resultado invalidado."""
    async def _comprobar(vista, cliente):
        accion = vista._calcular if herramienta == 'leontief' else vista._analizar
        boton = ui.button('prueba')
        await accion(boton)
        assert vista.ultimo_resultado is not None
        tarea = asyncio.create_task(accion(boton))
        await asyncio.sleep(0)
        _editar_y_restaurar(vista, herramienta)
        await tarea
        assert vista.ultimo_resultado is None
        assert not boton._props.get('loading', False)
        assert not any(elemento.text == 'Calculando…' for elemento in vista.contenedor_resultados.descendants()
                       if isinstance(elemento, ui.label))
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))


@pytest.mark.parametrize('herramienta', ['leontief', 'transformaciones'])
def test_cancelacion_del_manejador_retira_loading_y_publica_estado(monkeypatch, herramienta):
    """El manejador real libera el botón y muestra cancelación cuando la captura sigue vigente."""
    async def _comprobar(vista, cliente):
        inicio = asyncio.Event()
        async def _trabajar(*argumentos):
            inicio.set()
            await asyncio.Event().wait()
        monkeypatch.setattr(run, 'io_bound', _trabajar)
        accion = vista._calcular if herramienta == 'leontief' else vista._analizar
        boton = ui.button('prueba')
        tarea = asyncio.create_task(accion(boton))
        await inicio.wait()
        tarea.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarea
        assert not boton._props.get('loading', False)
        assert vista.ultimo_resultado is None
        assert any('Cálculo cancelado' in elemento.text for elemento in vista.contenedor_resultados.descendants()
                   if isinstance(elemento, ui.label))
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))
