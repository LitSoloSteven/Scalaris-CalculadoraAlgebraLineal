"""Encabezado, sugerencias y estados de la vista real de Determinantes."""
import asyncio
from types import SimpleNamespace

import pytest
from nicegui import ui

from src.frontend import textos
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("metodo", ["laplace", "lu"])
@pytest.mark.parametrize("datos,singular", [([["2", "0"], ["0", "3"]], False), ([["1", "2"], ["2", "4"]], True)])
def test_resultado_determinante_tiene_paridad_y_senales(monkeypatch, metodo, datos, singular):
    """Comprueba el resultado visible, las fases y el estado de Glosa sin llamar al proveedor."""
    async def comprobar(vista, cliente):
        """Calcula e invalida una captura con controles reales."""
        assert vista.obtener_senales_ia().estado == "sin_resultado"
        vista.panel_matriz.cargar_matriz(datos)
        vista.metodos_determinante.set_value(metodo)
        await vista.calcular(SimpleNamespace(sender=ui.button("Calcular")))
        resultado = vista.ultimo_resultado
        assert resultado["tiempo_transcurrido_segundos"] >= 0 and resultado["dimension"] == 2
        assert vista.obtener_senales_ia().estado == ("singular" if singular else "exito")
        assert metodo in vista.obtener_senales_ia().banderas
        assert ("rango_deficiente" in vista.obtener_senales_ia().banderas) is singular
        elementos = list(vista.contenedor_resultados.descendants())
        expansiones = {elemento.text for elemento in elementos if isinstance(elemento, ui.expansion)}
        assert {textos.PASOS_AYUDA_TITULO, textos.PASOS_INDICE_TITULO, textos.RESULTADO_INTERPRETACION} <= expansiones
        assert any(isinstance(elemento, ui.html) and r"\det(A)" in elemento.content for elemento in elementos)
        assert any(isinstance(elemento, ui.button) and elemento.text == textos.PDF_EXPORTAR for elemento in elementos)
        vista.panel_matriz.cargar_matriz([["1/0", "0"], ["0", "1"]])
        senales = vista.obtener_senales_ia()
        assert senales.estado == "sin_resultado" and senales.invalida.foco == (0, 0)
    asyncio.run(construir_pagina(monkeypatch, "determinantes", comprobar))
