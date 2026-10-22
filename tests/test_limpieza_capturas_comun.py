"""Contrato de limpieza real en las diez vistas y las tres escenas geométricas."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from nicegui import ui
from src.frontend.componentes.limpieza_captura import LimpiezaCaptura
from tests.comun_construccion_vistas import construir_pagina

HERRAMIENTAS = ['sistemas', 'inversa', 'matrices', 'vectores', 'determinantes',
                'leontief', 'transformaciones', 'visualizador', 'bases', 'romanos']


def llenar_captura(vista, herramienta):
    """Introduce ceros escritos o textos largos sin ejecutar el dominio."""
    if herramienta == 'sistemas':
        vista.cuadricula.entradas_coeficientes[0][0].set_value('0')
    elif herramienta in ('inversa', 'determinantes'):
        panel = vista.panel_matriz_cuadrada if herramienta == 'inversa' else vista.panel_matriz
        panel.cargar_matriz([['9' * 128] * 50] * 50)
    elif herramienta == 'matrices':
        vista.entrada_expresion.set_value('A + B')
        for matriz in vista.panel_captura_matrices.matrices.values():
            matriz['entradas'][0][0].set_value('17')
    elif herramienta == 'vectores':
        next(iter(vista.panel_vectorial.vectores.values()))['celdas'][0] = '0'
    elif herramienta in ('leontief', 'transformaciones'):
        for entrada in vista._campos_captura():
            entrada.set_value('0')
    else:
        llenar_captura_auxiliar(vista, herramienta)


def llenar_captura_auxiliar(vista, herramienta):
    """Introduce datos en las escenas geométricas y las entradas numéricas."""
    if herramienta == 'visualizador':
        if vista.escena == 'rectas-planos':
            vista.cuadricula.entradas_coeficientes[0][0].set_value('0')
        else:
            next(iter(vista._panel_vectorial_activo().vectores.values()))['celdas'][0] = '0'
    elif herramienta == 'bases':
        vista.entrada_valor.set_value('9' * 10000)
    elif herramienta == 'romanos':
        vista.entrada_a.set_value('M' * 10000)
        vista.entrada_b.set_value('I' * 10000)


@pytest.mark.parametrize('herramienta', HERRAMIENTAS)
def test_flujo_unico_y_vaciado_real(monkeypatch, herramienta):
    """Confirma datos extremos y vacía incluso cuando falla el transporte JS."""
    async def comprobar(vista, cliente):
        """Comprueba el botón y ejecuta el contrato sobre controles NiceGUI reales."""
        botones = [elemento for elemento in cliente.elements.values()
                   if elemento._props.get('id') == 'boton-limpiar-principal']
        assert len(botones) == 1 and botones[0]._props['aria-label'] == 'Limpiar'
        assert botones[0]._style['flex-shrink'] == '0'
        control = LimpiezaCaptura(vista, lambda: not cliente.is_deleted)
        assert vista.esta_completamente_vacio()
        aviso = Mock()
        monkeypatch.setattr(ui, 'notify', aviso)
        await control.confirmar()
        aviso.assert_called_once_with('No hay datos que limpiar.', type='info', position='top')
        assert control.dialogo is None
        llenar_captura(vista, herramienta)
        assert not vista.esta_completamente_vacio()
        vista._huella_resultado = 'huella antigua'
        detenido = Mock()
        vista.reproductor_pasos = SimpleNamespace(detener=detenido)
        panel = getattr(vista, 'panel_ia', None)
        foco = Mock()
        if panel:
            monkeypatch.setattr(panel, 'limpiar_foco_explicacion', foco)
        await control.confirmar()
        assert control.dialogo.value
        monkeypatch.setattr(ui, 'run_javascript', AsyncMock(side_effect=TimeoutError()))
        await control.ejecutar()
        assert vista.esta_completamente_vacio() and vista._huella_resultado is None
        resultado = getattr(vista, 'resultado_actual', None) if herramienta == 'vectores' else vista.ultimo_resultado
        assert resultado is None and not control.dialogo.value
        detenido.assert_called_once()
        if panel:
            foco.assert_called()
        await asyncio.sleep(0)
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize('escena', ['rectas-planos', 'vectores', 'combinacion'])
def test_visualizador_cancela_y_reinicia_figura(monkeypatch, escena):
    """El vaciado de cada escena cancela tareas y retira todos los datos de Plotly."""
    async def comprobar(vista, cliente):
        """Retira tanto figuras como el cálculo diferido de la captura."""
        llenar_captura(vista, 'visualizador')
        vista._programar_actualizacion()
        tarea = vista._tarea_previa
        vista.ultimo_hash_entrada = 17
        vista.ultimo_resultado = {'estado': 'EXITO'}
        vista._huella_resultado = 'huella'
        vista._primer_dibujo = False
        vista._elemento_plotly = object()
        vista.limpiar_todo()
        await asyncio.sleep(0)
        assert tarea.cancelled()
        assert vista._tarea_previa is None and vista.ultimo_hash_entrada is None
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert vista._primer_dibujo and vista._elemento_plotly is None
        assert vista.esta_completamente_vacio()
    asyncio.run(construir_pagina(monkeypatch, 'visualizador', comprobar, {'escena': escena}))


def test_desmontaje_y_doble_confirmacion(monkeypatch):
    """Una animación pendiente no limpia una vista desmontada ni se duplica."""
    async def comprobar():
        """Controla la respuesta del cliente para simular navegación durante la espera."""
        captura = SimpleNamespace(limpiar_todo=Mock())
        montada = [True]
        control = LimpiezaCaptura(captura, lambda: montada[0])
        inicio, continuar = asyncio.Event(), asyncio.Event()
        async def animar(*argumentos, **opciones):
            """Retiene la respuesta de la animación hasta completar el desmontaje."""
            inicio.set()
            await continuar.wait()
        monkeypatch.setattr(ui, 'run_javascript', animar)
        primera = asyncio.create_task(control.ejecutar())
        await inicio.wait()
        await control.ejecutar()
        montada[0] = False
        continuar.set()
        await primera
        captura.limpiar_todo.assert_not_called()
        assert not control._limpiando
    asyncio.run(comprobar())
