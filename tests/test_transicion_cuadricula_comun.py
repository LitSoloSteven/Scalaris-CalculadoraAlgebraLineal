"""Secuencia común, exclusión de pulsaciones y recuperación ante fallos de captura."""
import asyncio
from unittest.mock import AsyncMock
import pytest
from nicegui import ui, Client
from src.frontend.componentes.cuadricula_base import CambioCuadricula, ejecutar_transicion_cuadricula


def _crear_controles():
    cliente = Client(ui.page('/prueba_transicion'))
    with cliente:
        boton, limitado = ui.button('Cambiar'), ui.button('Límite')
    limitado.disable()
    return cliente, boton, limitado


def test_transicion_descarta_pulsaciones_y_mantiene_bloqueo_hasta_entrada():
    """La operación se aplica una vez y los botones permanecen bloqueados durante ambas animaciones."""
    async def comprobar():
        """Observa la secuencia con una salida deliberadamente pendiente."""
        cliente, boton, _ = _crear_controles()
        salida, estado, sucesos = asyncio.Event(), {}, []

        async def animar(accion, selector):
            """Registra el bloqueo en cada fase del cambio."""
            assert not boton.enabled
            sucesos.append(accion)
            if accion == 'Salida':
                await salida.wait()

        cambio = CambioCuadricula(('salida', 'entrada'), animar)
        aplicar = lambda: sucesos.append('aplicar')
        restaurar = lambda: sucesos.append('restaurar')
        try:
            primera = asyncio.create_task(ejecutar_transicion_cuadricula(estado, cambio, aplicar, (boton,), restaurar))
            await asyncio.sleep(0)
            await ejecutar_transicion_cuadricula(estado, cambio, aplicar, (boton,), restaurar)
            salida.set()
            await primera
            assert sucesos == ['Salida', 'aplicar', 'Entrada', 'restaurar']
            assert boton.enabled and not estado['_transicion_activa']
        finally:
            cliente.delete()
    asyncio.run(comprobar())


@pytest.mark.parametrize('fallo', ['animacion', 'renderizado', 'cancelacion'])
def test_fallos_y_cancelacion_restauran_visibilidad_y_controles(monkeypatch, fallo):
    """La limpieza se ejecuta también al cancelar una operación o fallar la reconstrucción."""
    transporte = AsyncMock()
    monkeypatch.setattr(ui, 'run_javascript', transporte)

    async def comprobar():
        """Inyecta un fallo conservando un botón inicialmente deshabilitado."""
        cliente, boton, limitado = _crear_controles()
        estado, restauraciones = {}, []

        async def animar(accion, selector):
            """Puede interrumpir la salida sin mutar datos."""
            if fallo == 'animacion':
                raise RuntimeError('animación simulada')
            if fallo == 'cancelacion':
                raise asyncio.CancelledError()

        def aplicar():
            """Simula una reconstrucción fallida."""
            raise RuntimeError('renderizado simulado')

        try:
            with pytest.raises(asyncio.CancelledError if fallo == 'cancelacion' else RuntimeError):
                await ejecutar_transicion_cuadricula(estado, CambioCuadricula(('salida', ''), animar), aplicar,
                                                    (boton, limitado), lambda: restauraciones.append(True))
            assert boton.enabled and not limitado.enabled
            assert restauraciones == [True] and not estado['_transicion_activa']
            assert 'restaurarCeldas' in transporte.call_args.args[0]
        finally:
            cliente.delete()
    asyncio.run(comprobar())
