"""Acciones de resultados y recorrido completo de Determinantes a Inversa."""
import asyncio
from types import SimpleNamespace
from urllib.parse import urlsplit
import pytest
from nicegui import ui

from src.frontend.componentes import transferencia
from src.frontend.componentes.acciones_matriz import renderizar_acciones_matriz
from tests.comun_calculos_vistas import calcular_minimo
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_transferencia_matriz import preparar_ruta_lu, activar_boton, token_desde_url


def test_determinante_abre_inversa_con_la_misma_matriz(monkeypatch):
    """El botón real crea una transferencia que la ruta de Inversa carga sin calcular."""
    destinos = []
    monkeypatch.setattr(ui.navigate, "to", destinos.append)
    datos = [["2", "1/3"], ["0", "3"]]

    async def calcular(vista, cliente):
        """Calcula el determinante y activa el destino de la captura publicada."""
        vista.panel_matriz.cargar_matriz(datos)
        await vista.calcular(SimpleNamespace(sender=ui.button("Calcular")))
        assert vista.ultimo_resultado["estado"] == "EXITO"
        boton = next(elemento for elemento in vista.contenedor_resultados.descendants()
                     if elemento._props.get("data-destino-matriz") == "inversa")
        activar_boton(boton)
        assert urlsplit(destinos[0]).path == "/algebra-lineal/inversa"

    async def recibir(vista, cliente):
        """Comprueba la carga exacta de la matriz en el panel de destino."""
        assert vista.panel_matriz_cuadrada.obtener_datos_matriz() == datos
        assert vista.ultimo_resultado is None

    asyncio.run(construir_pagina(monkeypatch, "determinantes", calcular))
    asyncio.run(construir_pagina(monkeypatch, "inversa", recibir,
                                {"handoff": token_desde_url(destinos[0])}))


@pytest.mark.parametrize("singular", [False, True])
def test_inversa_transfiere_a_original_aunque_el_editor_cambie(monkeypatch, singular):
    """Las acciones del resultado conservan A y la acción especial conserva A inversa."""
    destinos = []
    monkeypatch.setattr(ui.navigate, "to", destinos.append)
    datos = [["1", "2"], ["2", "4"]] if singular else [["2", "0"], ["0", "3"]]

    async def comprobar(vista, cliente):
        """Edita después del cálculo y comprueba los datos de ambas acciones."""
        vista.panel_matriz_cuadrada.cargar_matriz(datos)
        await vista.calcular(ui.button("Calcular"))
        assert vista.ultimo_resultado["estado"] == ("SINGULAR" if singular else "EXITO")
        elementos = list(vista.contenedor_resultados.descendants())
        boton = next(elemento for elemento in elementos
                     if elemento._props.get("data-destino-matriz") == "sistemas")
        vista.panel_matriz_cuadrada.cargar_matriz([["9"]])
        activar_boton(boton)
        carga = transferencia.consumir_matriz(token_desde_url(destinos[-1]), dimension_maxima=10)
        assert carga.datos == datos
        if not singular:
            especial = next(elemento for elemento in elementos
                            if isinstance(elemento, ui.button) and elemento.text == "Resolver A·x = b con esta A")
            activar_boton(especial)
            carga = transferencia.consumir_matriz(token_desde_url(destinos[-1]), dimension_maxima=10)
            assert carga.datos == [["1/2", "0"], ["0", "1/3"]]
    asyncio.run(construir_pagina(monkeypatch, "inversa", comprobar))


@pytest.mark.parametrize("herramienta", ["sistemas", "matrices", "leontief", "transformaciones"])
def test_otros_origenes_publican_destinos_tras_exito(monkeypatch, herramienta):
    """Los cálculos exitosos montan destinos sin ofrecer la herramienta de origen."""
    async def comprobar(vista, cliente):
        """Ejecuta el cálculo mínimo de cada módulo con matemáticas reales."""
        await calcular_minimo(herramienta, vista)
        destinos = {elemento._props["data-destino-matriz"] for elemento in vista.contenedor_resultados.descendants()
                    if "data-destino-matriz" in elemento._props}
        assert destinos and herramienta not in destinos
        assert "determinantes" in destinos and "inversa" in destinos
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize("datos,esperados", [([["1", "2"], ["2", "4"]], True),
                                             ([["1", "2", "3"]], True), ([["1/0"]], False)])
def test_lu_publica_solo_destinos_transferibles(monkeypatch, datos, esperados):
    """LU singular y rectangular ofrecen acciones; los errores carecen de botones."""
    preparar_ruta_lu(monkeypatch)
    async def comprobar(vista, cliente):
        """Calcula la captura y comprueba las acciones asociadas al resultado."""
        vista.panel_matriz.cargar_matriz(datos)
        await vista.calcular(SimpleNamespace(sender=ui.button("Calcular")))
        botones = [elemento for elemento in vista.contenedor_resultados.descendants()
                   if "data-destino-matriz" in elemento._props]
        assert bool(botones) is esperados
    asyncio.run(construir_pagina(monkeypatch, "factorizacion_lu", comprobar))


def test_acciones_toman_una_copia_independiente(monkeypatch):
    """El componente aísla los datos del editor antes de activar un destino."""
    destinos = []
    monkeypatch.setattr(ui.navigate, "to", destinos.append)
    async def comprobar(vista, cliente):
        """Muta la lista productora antes de activar uno de los botones creados."""
        datos = [["1/1001"]]
        with ui.column() as contenedor:
            renderizar_acciones_matriz("determinantes", datos)
        datos[0][0] = "99"
        boton = next(elemento for elemento in contenedor.descendants()
                     if elemento._props.get("data-destino-matriz") == "inversa")
        activar_boton(boton)
        assert transferencia.consumir_matriz(token_desde_url(destinos[-1]), dimension_maxima=50).datos == [["1/1001"]]
    asyncio.run(construir_pagina(monkeypatch, "determinantes", comprobar))
