"""Restauración completa de expresiones y familias vectoriales desde historial."""
import asyncio
import copy

import pytest

from src.frontend.vistas.sesion_capturas import obtener_captura_sesion, restaurar_captura
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_calculos_vistas import calcular_minimo


@pytest.mark.parametrize("herramienta", ["matrices", "vectores"])
def test_historial_conserva_captura_independiente_y_restaura_sin_calcular(monkeypatch, herramienta):
    """El resultado registra una captura completa que puede restaurarse después de editar."""
    async def comprobar(vista, cliente):
        """Ejercita el historial de la vista montada y comprueba sus valores y opciones."""
        await calcular_minimo(herramienta, vista)
        sesion = vista.sesion_capturas
        assert len(sesion.registros) == 1 and sesion.previa.text
        guardada = copy.deepcopy(sesion.registros[0]["captura"])
        assert obtener_captura_sesion(vista, herramienta) == guardada
        if herramienta == "matrices":
            vista.entrada_expresion.set_value("A - A")
        else:
            vista.panel_vectorial.vectores["u"]["celdas"][0] = "99"
            vista.panel_vectorial.vectores["u"]["orientacion"] = "fila"
            vista._al_cambiar_vectores()
        assert sesion.registros[0]["captura"] == guardada
        restaurar_captura(vista, herramienta, guardada)
        assert obtener_captura_sesion(vista, herramienta) == guardada
        assert len(sesion.registros) == 1
        assert (vista.ultimo_resultado if herramienta == "matrices" else vista.resultado_actual) is None
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
