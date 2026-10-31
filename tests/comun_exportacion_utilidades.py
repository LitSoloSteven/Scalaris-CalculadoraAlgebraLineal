"""Escenarios reales y cambios de entrada para las utilidades exportables."""
import asyncio

from tests.comun_calculos_vistas import calcular_minimo
from tests.comun_construccion_vistas import construir_pagina

CASOS = ('bases', 'romanos', 'rectas-planos', 'vectores', 'combinacion')


def herramienta_de(caso):
    """Relaciona escenas y herramientas con las rutas reales del arnés."""
    return caso if caso in ('bases', 'romanos') else 'visualizador'


async def construir_utilidad(monkeypatch, caso, comprobar):
    """Construye la ruta pública con su escena solicitada sin sustituir controles."""
    parametros = {'escena': caso} if herramienta_de(caso) == 'visualizador' else {}
    await construir_pagina(monkeypatch, herramienta_de(caso), comprobar, parametros)


async def calcular_utilidad(caso, vista):
    """Calcula una entrada válida por la vista numérica o el controlador geométrico."""
    if caso in ('bases', 'romanos', 'rectas-planos'):
        await calcular_minimo(herramienta_de(caso), vista)
        return
    panel = vista.panel_vectores if caso == 'vectores' else vista.panel_combinacion
    for indice, vector in enumerate(panel.vectores.values()):
        vector['celdas'] = {posicion: str(int(posicion == indice % panel.dimension))
                            for posicion in range(panel.dimension)}
    await vista._actualizar_figura()
    assert vista.ultimo_resultado['estado'] == 'EXITO'


async def editar_utilidad(caso, vista):
    """Edita y restaura una entrada a través de sus notificaciones reales."""
    if caso == 'bases':
        original = vista.entrada_valor.value
        vista.entrada_valor.set_value('7')
        vista.entrada_valor.set_value(original)
    elif caso == 'romanos':
        original = vista.entrada_a.value
        vista.entrada_a.set_value('V')
        vista.entrada_a.set_value(original)
    else:
        vista._notificar_cambio_datos()
        vista._cancelar_actualizacion()
    await asyncio.sleep(0)
