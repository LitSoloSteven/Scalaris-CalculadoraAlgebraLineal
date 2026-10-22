"""La limpieza descarta cálculos iniciados antes de retirar sus entradas."""
import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from nicegui import ui
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('herramienta', ['bases', 'romanos', 'leontief', 'transformaciones'])
def test_limpieza_antes_de_calculo_pendiente(monkeypatch, herramienta):
    """La espera de carga no puede publicar resultados después de limpiar."""
    async def comprobar(vista, cliente):
        """Limpia en el primer cambio de tarea y exige no llamar al resolutor."""
        if herramienta == 'bases':
            vista.entrada_valor.set_value('42')
            nombre, iniciar = '_ejecutar_conversion', vista._convertir_boton
        elif herramienta == 'romanos':
            vista.entrada_a.set_value('X')
            nombre, iniciar = 'operar_romanos', vista._operar_desde_control
        else:
            nombre = '_calcular_nucleo' if herramienta == 'leontief' else '_analizar_nucleo'
            accion = vista._calcular if herramienta == 'leontief' else vista._analizar
            iniciar = lambda: accion(ui.button('Prueba'))
        calcular = Mock() if herramienta == 'romanos' else AsyncMock()
        monkeypatch.setattr(vista, nombre, calcular)
        tarea = asyncio.create_task(iniciar())
        await asyncio.sleep(0)
        vista.limpiar_todo()
        await tarea
        calcular.assert_not_called()
        assert vista.esta_completamente_vacio()
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        if herramienta == 'bases':
            assert vista.etiqueta_estado.text == 'Ingresa un número y pulsa Convertir.'
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_visualizacion_manual_cancelada_por_limpieza(monkeypatch):
    """El cálculo manual y el automático comparten la tarea cancelable de la escena."""
    async def comprobar(vista, cliente):
        """Retiene un dibujo manual y limpia antes de que pueda publicar."""
        inicio, continuar = asyncio.Event(), asyncio.Event()
        async def actualizar():
            """Simula la espera del trabajador o de la construcción de Plotly."""
            inicio.set()
            await continuar.wait()
            vista.ultimo_resultado = {'estado': 'EXITO'}
        monkeypatch.setattr(vista, '_actualizar_figura', actualizar)
        tarea = asyncio.create_task(vista._visualizar_captura())
        await inicio.wait()
        vista.limpiar_todo()
        continuar.set()
        with pytest.raises(asyncio.CancelledError):
            await tarea
        assert vista.ultimo_resultado is None and vista._tarea_previa is None
        assert vista._primer_dibujo and vista._elemento_plotly is None
    asyncio.run(construir_pagina(monkeypatch, 'visualizador', comprobar))


def test_conversion_diferida_no_restaura_datos(monkeypatch):
    """Una conversión diferida abandona su entrada después del vaciado."""
    async def comprobar(vista, cliente):
        """Retira datos mientras la conversión está esperando su antirrebote."""
        vista.entrada_valor.set_value('42')
        publicar = Mock()
        monkeypatch.setattr(vista, '_actualizar_estado_exitoso', publicar)
        tarea = asyncio.create_task(vista._ejecutar_conversion('42'))
        await asyncio.sleep(0)
        vista.limpiar_todo()
        assert await tarea is False
        publicar.assert_not_called()
        assert not vista.tiene_resultado
    asyncio.run(construir_pagina(monkeypatch, 'bases', comprobar))


def test_captura_bloqueada_hasta_finalizar_animacion(monkeypatch):
    """No permite cambiar la operación confirmada durante la espera del cliente."""
    async def comprobar(vista, cliente):
        """Mantiene inert durante la animación y lo retira tras un fallo de JS."""
        control = crear_boton_limpieza(vista, lambda: not cliente.is_deleted)
        inicio, continuar = asyncio.Event(), asyncio.Event()
        async def animar(*argumentos, **opciones):
            """Retiene el transporte para inspeccionar el bloqueo de la captura."""
            inicio.set()
            await continuar.wait()
            raise TimeoutError
        monkeypatch.setattr(ui, 'run_javascript', animar)
        tarea = asyncio.create_task(control.ejecutar())
        await inicio.wait()
        assert cliente.content._props['inert'] is True
        monkeypatch.setattr(ui, 'run_javascript', Mock())
        continuar.set()
        await tarea
        assert 'inert' not in cliente.content._props
        assert not control._limpiando
    asyncio.run(construir_pagina(monkeypatch, 'vectores', comprobar))
