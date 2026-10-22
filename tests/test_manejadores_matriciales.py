"""Manejadores reales y contratos cliente de las vistas matriciales."""
import asyncio
import inspect

import pytest
from nicegui import ui
from nicegui.events import ClickEventArguments

from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('herramienta,etiqueta', [('sistemas', 'Resolver'), ('inversa', 'Calcular inversa')])
def test_boton_real_utiliza_evento_nicegui(monkeypatch, herramienta, etiqueta):
    """Ejecuta el manejador registrado con emisor y cliente de la API real instalada."""
    original = ui.button
    botones = {}
    def crear_boton(*argumentos, **opciones):
        """Conserva cada boton real y su manejador tal como la vista lo registra."""
        boton = original(*argumentos, **opciones)
        if argumentos and argumentos[0] == etiqueta:
            botones[etiqueta] = (boton, opciones['on_click'])
        return boton
    monkeypatch.setattr(ui, 'button', crear_boton)
    async def comprobar(vista, cliente):
        """Invoca la accion de la vista con un evento del framework."""
        if herramienta == 'sistemas':
            vista.cuadricula.cargar_datos([['2']], ['1'])
        else:
            vista.panel_matriz_cuadrada.cargar_matriz([['2']])
        boton, manejador = botones[etiqueta]
        respuesta = manejador(ClickEventArguments(sender=boton, client=cliente))
        assert inspect.isawaitable(respuesta)
        await respuesta
        assert vista.ultimo_resultado['estado'] in ('EXITO', 'SOLUCION_UNICA')
        assert boton._props['loading'] == 'false'
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_visibilidad_sincronizacion_responde_a_celdas_y_ecuaciones(monkeypatch):
    """Las guardas de visibilidad usan las propiedades canonicas de ambos botones."""
    async def comprobar(vista, cliente):
        """Recorre captura vacia, entrada matricial y entrada de ecuaciones."""
        vista.actualizar_botones_sincronizacion()
        assert not vista.boton_desde_matriz.visible
        assert not vista.boton_desde_ecuaciones.visible
        vista.cuadricula.entradas_coeficientes[0][0].set_value('1')
        vista.actualizar_botones_sincronizacion()
        assert vista.boton_desde_matriz.visible
        vista.entradas_ecuaciones[0].set_value('x = 1')
        vista.actualizar_botones_sincronizacion()
        assert vista.boton_desde_ecuaciones.visible
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))


def test_vista_previa_inversa_publica_ambos_identificadores_mathjax(monkeypatch):
    """Los bloques de A y [A|I] comparten los identificadores enviados al cliente."""
    async def comprobar(vista, cliente):
        """Exige cada id dentro del HTML real renderizado y la llamada selectiva."""
        vista.panel_matriz_cuadrada.cargar_matriz([['1001/1000']])
        llamadas = []
        monkeypatch.setattr(ui, 'run_javascript', lambda codigo: llamadas.append(codigo))
        await vista._actualizar_vista_previa()
        contenido = '\n'.join(elemento.content for elemento in vista.contenedor_vista_previa.descendants() if isinstance(elemento, ui.html))
        for identificador in ('inversa-previa-matriz', 'inversa-previa-aumentada'):
            assert f'id="{identificador}"' in contenido
            assert identificador in llamadas[-1]
    asyncio.run(construir_pagina(monkeypatch, 'inversa', comprobar))
