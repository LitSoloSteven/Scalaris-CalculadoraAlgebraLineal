"""Recomendaciones automáticas y aceptación explícita con controles NiceGUI reales."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import ui
from src.frontend.componentes.selector_opciones import SelectorOpciones
from src.frontend.controladores.operaciones_matrices.recomendacion_determinante import metodo_recomendado_disponible
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('respuesta,actual,disponible', [
    (None, 'lu', None), ({}, 'lu', None), ({'estado': 'ERROR'}, 'lu', None),
    ({'estado': 'EXITO', 'metodo_recomendado': 'lu'}, 'lu', None),
    ({'estado': 'EXITO', 'metodo_recomendado': 'otro'}, 'lu', None),
    ({'estado': 'EXITO', 'metodo_recomendado': 'laplace'}, 'lu', 'laplace'),
    ({'estado': 'EXITO', 'metodo_recomendado': 'lu'}, 'laplace', 'lu'),
])
def test_accion_exige_recomendacion_valida_y_distinta(respuesta, actual, disponible):
    """Vacío, error, método desconocido o coincidente no ofrecen una acción."""
    assert metodo_recomendado_disponible(respuesta, actual) == disponible


def test_vacio_selector_y_teclado_sin_historial(monkeypatch):
    """La página vacía orienta y monta las herramientas con el historial vacío."""
    async def comprobar(vista, cliente):
        """Comprueba componentes compartidos, nombres y recursos del teclado."""
        assert isinstance(vista.metodos_determinante, SelectorOpciones)
        assert vista.metodos_determinante.value == 'lu'
        assert set(vista.metodos_determinante.botones) == {'laplace', 'lu'}
        assert vista.recomendacion.tarea is None and vista.recomendacion.respuesta is None
        assert vista.recomendacion.contenedor._props['role'] == 'status'
        assert vista.recomendacion.contenedor._props['aria-live'] == 'polite'
        assert not vista.recomendacion.boton_usar.visible
        pestanas = {elemento._props['name'] for elemento in vista.pestanas_herramientas.descendants()
                    if isinstance(elemento, ui.tab)}
        assert pestanas == {'teclado', 'vista_previa', 'historial'}
        assert vista.pestanas_herramientas.value == 'teclado'
        assert not vista.historial
        assert '/assets/js/calculadora.js' in cliente.head_html
        assert sum(isinstance(elemento, ui.button) and elemento.text == '7'
                   for elemento in cliente.elements.values()) == 1
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


def test_aceptar_recomendacion_invalida_sin_imponer_eleccion(monkeypatch):
    """La recomendación no cambia LU hasta que la persona decide aceptarla."""
    async def comprobar(vista, cliente):
        """Acepta la sugerencia y retira resultado, reproductor, huella y foco de Glosa."""
        vista.panel_matriz.cargar_matriz([['1', '0'], ['0', '1']])
        await vista.recomendacion.tarea
        assert vista.recomendacion.respuesta['metodo_recomendado'] == 'laplace'
        assert vista.metodos_determinante.value == 'lu' and vista.recomendacion.boton_usar.visible
        vista.ultimo_resultado = {'estado': 'EXITO'}
        vista._huella_resultado = 'anterior'
        detener, limpiar_foco = Mock(), Mock()
        vista.reproductor_pasos = SimpleNamespace(detener=detener)
        monkeypatch.setattr(vista.panel_ia, 'limpiar_foco_explicacion', limpiar_foco)
        vista.recomendacion.usar_recomendado()
        assert vista.metodos_determinante.value == 'laplace'
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert not vista.recomendacion.boton_usar.visible
        detener.assert_called_once()
        limpiar_foco.assert_called_once()
        vista.metodos_determinante.set_value('lu')
        assert vista.recomendacion.boton_usar.visible
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


def test_error_captura_y_limpieza_conservan_estados_accesibles(monkeypatch):
    """La entrada hostil se presenta como texto de error y desaparece al limpiar."""
    async def comprobar(vista, cliente):
        """Introduce una celda inválida y verifica el mensaje del controlador."""
        vista.panel_matriz.celdas[0][0].set_value('<script>entrada inválida</script>')
        await vista.recomendacion.tarea
        assert vista.recomendacion.respuesta['estado'] == 'ERROR'
        assert vista.recomendacion.contenedor._props['role'] == 'alert'
        assert not vista.recomendacion.boton_usar.visible
        etiquetas = [elemento.text for elemento in vista.recomendacion.mensajes.descendants()
                     if isinstance(elemento, ui.label)]
        assert vista.recomendacion.respuesta['mensaje'] in etiquetas
        assert not any(isinstance(elemento, ui.html) for elemento in vista.recomendacion.mensajes.descendants())
        vista.limpiar_todo()
        assert vista.recomendacion.respuesta is None and vista.recomendacion.tarea is None
        assert vista.recomendacion.contenedor._props['role'] == 'status'
        assert not vista.recomendacion.boton_usar.visible
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))


def test_cincuenta_por_cincuenta_conserva_limites_legibles(monkeypatch):
    """La recomendación grande no calcula un determinante ni recorta la advertencia."""
    async def comprobar(vista, cliente):
        """Usa una diagonal de orden 50 y conserva el texto completo del backend."""
        datos = [['1' if fila == columna else '0' for columna in range(50)] for fila in range(50)]
        vista.panel_matriz.cargar_matriz(datos)
        await vista.recomendacion.tarea
        respuesta = vista.recomendacion.respuesta
        assert respuesta['estado'] == 'EXITO' and respuesta['metodo_recomendado'] == 'lu'
        assert not vista.recomendacion.boton_usar.visible and vista.ultimo_resultado is None
        etiquetas = [elemento.text for elemento in vista.recomendacion.mensajes.descendants()
                     if isinstance(elemento, ui.label)]
        assert respuesta['limites_cofactores'] in etiquetas
        assert '10000' in respuesta['limites_cofactores']
    asyncio.run(construir_pagina(monkeypatch, 'determinantes', comprobar))
