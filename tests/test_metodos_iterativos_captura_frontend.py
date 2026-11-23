"""Contratos de captura de sistemas iterativos en la interfaz."""
import asyncio
from unittest.mock import AsyncMock

import pytest
from nicegui import Client, ui

from src.frontend.componentes.captura.ecuaciones.cuadricula_ecuaciones import CuadriculaEcuaciones


def test_cuadricula_cuadrada_redimensiona_junta_y_notifica(monkeypatch):
    """Conserva las celdas comunes, elimina el borde y notifica una vez por cambio."""
    monkeypatch.setattr(ui, 'run_javascript', AsyncMock())

    async def comprobar():
        cliente = Client(ui.page('/prueba-cuadricula-iterativa'))
        try:
            with cliente:
                cuadricula = CuadriculaEcuaciones(2, cuadrada=True)
                cuadricula.construir_contenedor_cuadricula()
                dimensiones = []
                cuadricula.al_cambiar_dimension = lambda *forma: dimensiones.append(forma)
                assert cuadricula.boton_agregar_fila is None
                cuadricula.entradas_coeficientes[0][0].set_value('1/1001')
                await cuadricula.ajustar_tamano(incremento_columnas=1)
                cuadricula.entradas_coeficientes[0][2].set_value('7')
                await cuadricula.ajustar_tamano(incremento_columnas=-1)
                await cuadricula.ajustar_tamano(incremento_columnas=1)
                assert dimensiones == [(3, 3), (2, 2), (3, 3)]
                assert cuadricula.obtener_datos_matriz()[0][0] == ['1/1001', '0', '0']
                with pytest.raises(ValueError, match='matriz cuadrada'):
                    cuadricula.cargar_datos([['1', '2']], ['3'])
                assert (cuadricula.filas, cuadricula.columnas) == (3, 3)
        finally:
            cliente.delete()

    asyncio.run(comprobar())
