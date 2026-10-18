"""Invocación de cálculos matriciales con el botón real de cada sesión de pruebas."""
from nicegui import ui


async def ejecutar_calculo_sesion(vista, herramienta):
    """Crea el botón, espera el cálculo correspondiente y devuelve el mismo control."""
    boton = ui.button('Calcular')
    if herramienta == 'sistemas':
        await vista.resolver_sistema(boton)
    else:
        await vista.calcular(boton)
    return boton
