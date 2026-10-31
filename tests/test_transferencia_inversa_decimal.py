"""Transferencia de la captura decimal original en el límite de longitud."""
import asyncio
from nicegui import ui

from src.backend.constantes import LONGITUD_MAXIMA_CELDA
from src.frontend.componentes.transferencia import consumir_matriz
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_transferencia_matriz import activar_boton, token_desde_url


def test_decimal_limite_no_se_expande_a_fraccion_al_transferir(monkeypatch):
    """Un decimal válido conserva su texto y sigue siendo aceptado por el receptor."""
    decimal = "0." + "0" * (LONGITUD_MAXIMA_CELDA - 3) + "1"
    destinos = []
    monkeypatch.setattr(ui.navigate, "to", destinos.append)

    async def comprobar(vista, cliente):
        """Invierte, edita y transfiere la captura estable de longitud máxima."""
        vista.panel_matriz_cuadrada.cargar_matriz([[decimal]])
        await vista.calcular(ui.button("Calcular"))
        assert vista.ultimo_resultado["estado"] == "EXITO"
        assert len(str(vista.ultimo_resultado["matriz_a"].datos[0][0])) > LONGITUD_MAXIMA_CELDA
        boton = next(elemento for elemento in vista.contenedor_resultados.descendants()
                     if elemento._props.get("data-destino-matriz") == "determinantes")
        vista.panel_matriz_cuadrada.cargar_matriz([["2"]])
        activar_boton(boton)
        carga = consumir_matriz(token_desde_url(destinos[0]), dimension_maxima=50)
        assert carga.estado == "exito" and carga.datos == [[decimal]]
    asyncio.run(construir_pagina(monkeypatch, "inversa", comprobar))
