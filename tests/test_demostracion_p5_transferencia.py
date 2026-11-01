"""Recorrido de matrices a transformaciones con transferencia y cálculo reales."""
import asyncio
from fractions import Fraction
from urllib.parse import parse_qs, urlsplit

import pytest
from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.componentes import acciones_matriz, transferencia
from src.frontend.vistas.operaciones_matrices.carga_modelos import cargar_captura_modelo
from tests.comun_construccion_vistas import construir_pagina

MATRIZ_FRACCIONARIA = [["1/2", "1/3"], ["2/5", "-1/7"]]
VECTOR_ORIGINAL = ["1/2", "1/3"]


@pytest.mark.parametrize("rectangular", [False, True])
def test_transferir_captura_calcular_y_restaurar_sin_perder_fracciones(monkeypatch, rectangular):
    """Conecta ambas rutas y contrasta resultado exacto, gráfica y sesión restaurada."""
    matriz = [list(fila) for fila in MATRIZ_FRACCIONARIA]
    esperado = ["13/36", "16/105"]
    if rectangular:
        matriz.append(["0", "1/11"])
        esperado.append("1/33")

    async def recorrer():
        """Conserva solo la navegación como transporte simulado entre las rutas reales."""
        direccion = await _evaluar_y_transferir(monkeypatch, matriz)
        assert urlsplit(direccion).path == "/algebra-lineal/transformaciones"
        token = parse_qs(urlsplit(direccion).query)["handoff"][0]
        with monkeypatch.context() as contexto:
            await construir_pagina(contexto, "transformaciones",
                                   lambda vista, cliente: _comprobar_destino(vista, matriz, esperado),
                                   {"handoff": token})
        assert transferencia.consumir_matriz(token, dimension_maxima=8).estado == "ausente"
    asyncio.run(recorrer())


async def _evaluar_y_transferir(monkeypatch, matriz: list[list[str]]) -> str:
    navegaciones = []

    async def comprobar(vista, cliente):
        """Evalúa A+A y activa el botón real que transfiere la captura A, no su suma."""
        vista.panel_captura_matrices.cargar_datos({"A": matriz})
        vista.entrada_expresion.set_value("A+A")
        await vista.evaluar_expresion(ui.button("Evaluar"))
        resultado = vista.ultimo_resultado
        assert resultado["estado"] == "EXITO" and resultado["pasos_segmento"]
        duplicada = [[str(2 * Fraction(valor)) for valor in fila] for fila in matriz]
        assert resultado["matriz_resultado"]["datos"] == duplicada
        boton = next(elemento for elemento in vista.contenedor_resultados.descendants()
                     if elemento._props.get("data-destino-matriz") == "transformaciones")
        escucha = next(escucha for escucha in boton._event_listeners.values() if escucha.type == "click")
        escucha.handler(None)
        assert len(navegaciones) == 1

    with monkeypatch.context() as contexto:
        contexto.setattr(acciones_matriz.ui.navigate, "to", navegaciones.append)
        await construir_pagina(contexto, "matrices", comprobar)
    return navegaciones[0]


async def _comprobar_destino(vista, matriz: list[list[str]], esperado: list[str]) -> None:
    assert [[entrada.value for entrada in fila] for fila in vista.entradas_coeficientes] == matriz
    assert vista.ultimo_resultado is None
    vista.selector_modo.set_value(textos.MODO_APLICACION)
    for entrada, valor in zip(vista.entradas_vector_original, VECTOR_ORIGINAL):
        entrada.set_value(valor)
    await vista._analizar(vista.boton_calcular)
    resultado = vista.ultimo_resultado
    assert resultado["estado"] == "EXITO" and resultado["verificacion"] is True
    assert resultado["matriz_a"]["datos"] == matriz
    assert resultado["vector_original"]["exacta"] == VECTOR_ORIGINAL
    assert resultado["vector_transformado"]["exacta"] == esperado
    graficas = [elemento for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.plotly)]
    assert len(graficas) == (1 if len(matriz) == 2 else 2)
    transformada = graficas[-1].figure["data"][1 if len(matriz) == 2 else 0]
    assert transformada["x"][-1] == pytest.approx(float(Fraction(esperado[0])))
    assert transformada["y"][-1] == pytest.approx(float(Fraction(esperado[1])))
    assert transformada["customdata"][-1] == "(" + ", ".join(esperado) + ")"
    if len(matriz) == 3:
        assert transformada["z"][-1] == pytest.approx(1 / 33)
    captura = vista.historial[0]["captura"]
    assert captura["matriz_transformacion"] == matriz and captura["vector_original"] == VECTOR_ORIGINAL
    assert len(vista.reproductor_pasos.pasos) == 2 * len(matriz) + 3
    vista.entradas_vector_original[0].set_value("7")
    assert vista.ultimo_resultado is None
    cargar_captura_modelo(vista, captura)
    await vista._analizar(vista.boton_calcular)
    assert vista.ultimo_resultado["vector_transformado"]["exacta"] == esperado
