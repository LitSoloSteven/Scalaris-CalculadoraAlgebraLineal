"""Montaje real y cálculo mínimo de las diez páginas registradas de Scalaris."""
import asyncio
from unittest.mock import Mock

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


@pytest.mark.parametrize("herramienta", VISTAS_RUTAS)
def test_cada_ruta_construye_su_vista_vacia(monkeypatch, herramienta):
    """El constructor diferido monta controles reales sin referencias inexistentes."""
    async def comprobar(vista, cliente):
        """Comprueba los datos y el estado del escenario de la prueba."""
        assert not cliente.is_deleted
        assert vista is not None
        etiquetas = [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.label)]
        assert etiquetas
        assert not any(isinstance(elemento, ui.icon) and elemento._props.get("name") == "matriz_inversa"
                       for elemento in cliente.elements.values())
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize("herramienta", ["sistemas", "vectores", "matrices", "inversa", "leontief",
                                         "transformaciones", "bases", "romanos", "visualizador"])
def test_calculo_minimo_de_cada_vista(monkeypatch, herramienta):
    """Los manejadores reales terminan con un resultado válido y elementos visibles."""
    from tests.comun_calculos_vistas import calcular_minimo

    async def comprobar(vista, cliente):
        """Comprueba los datos y el estado del escenario de la prueba."""
        await calcular_minimo(herramienta, vista)
        assert not any("error inesperado" in elemento.text.casefold() for elemento in cliente.elements.values()
                       if isinstance(elemento, ui.label))
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_arnes_leontief_rechaza_resultado_sin_renderizado(monkeypatch):
    """Un backend exitoso no oculta la excepción posterior del renderizador."""
    from src.frontend.vistas.operaciones_matrices import mixin_calculo_leontief
    from tests.comun_calculos_vistas import calcular_leontief

    def fallar_renderizado(resultado):
        """Procesa fallar renderizado con los datos recibidos."""
        raise KeyError("campo_ausente_simulado")

    monkeypatch.setattr(mixin_calculo_leontief, "renderizar_resultado_leontief", fallar_renderizado)

    async def comprobar(vista, cliente):
        """Comprueba los datos y el estado del escenario de la prueba."""
        with pytest.raises(AssertionError):
            await calcular_leontief(vista)
        assert vista.ultimo_resultado["estado"] == "EXITO"
        etiquetas = [elemento.text for elemento in vista.contenedor_resultados.descendants()
                     if isinstance(elemento, ui.label)]
        assert any("Error inesperado" in texto for texto in etiquetas)
    asyncio.run(construir_pagina(monkeypatch, "leontief", comprobar))


def test_arnes_matricial_rechaza_resultado_sin_renderizado(monkeypatch):
    """La guarda común detecta errores capturados después de un cálculo exitoso."""
    from src.frontend.vistas.operaciones_matrices.mixin_resultados import MixinResultadosOperacionesMatrices

    def fallar_renderizado(vista, resultado):
        """Procesa fallar renderizado con los datos recibidos."""
        raise KeyError("campo_ausente_simulado")

    monkeypatch.setattr(MixinResultadosOperacionesMatrices, "_renderizar_resultado_final", fallar_renderizado)
    with pytest.raises(AssertionError):
        test_calculo_minimo_de_cada_vista(monkeypatch, "matrices")


@pytest.mark.parametrize("herramienta", ["sistemas", "inversa"])
def test_transferencia_matricial_monta_y_carga_el_panel(monkeypatch, herramienta):
    """El import diferido y la carga consumen el token sin alias inexistentes."""
    from src.frontend.componentes.transferencia import guardar_matriz
    token = guardar_matriz("matrices", [["2", "0"], ["0", "3"]])

    async def comprobar(vista, cliente):
        """Comprueba los datos y el estado del escenario de la prueba."""
        if herramienta == "inversa": datos = vista.panel_matriz_cuadrada.obtener_datos_matriz()
        else: datos, _ = vista.cuadricula.obtener_datos_matriz()
        assert datos == [["2", "0"], ["0", "3"]]
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar, {"handoff": token}))


def test_matrices_adaptan_captura_real_al_contexto_ia(monkeypatch):
    """El contexto no trata una instancia Matriz como un diccionario heredado."""
    async def comprobar(vista, cliente):
        """Comprueba los datos y el estado del escenario de la prueba."""
        vista.panel_captura_matrices.cargar_datos({"A": [["1/3"]]})
        contexto = vista.obtener_contexto_ia()
        assert contexto.entrada["A"]["datos"] == [["1/3"]]
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_boton_invertir_matriz_utiliza_firma_real_del_componente(monkeypatch):
    """La acción recibe solo el nombre y obtiene su matriz desde la captura."""
    async def comprobar(vista, cliente):
        """Comprueba los datos y el estado del escenario de la prueba."""
        navegar = Mock()
        monkeypatch.setattr(ui.navigate, "to", navegar)
        vista.panel_captura_matrices.cargar_datos({"A": [["1/3"]]})
        vista.panel_captura_matrices.al_invertir("A")
        assert navegar.call_args.args[0].startswith("/algebra-lineal/inversa?handoff=")
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_accion_copiar_inversa_consume_el_modelo_real(monkeypatch):
    """Copiar la inversa conserva fracciones sin invocar un getter inexistente."""
    from tests.comun_calculos_vistas import calcular_inversa

    async def comprobar(vista, cliente):
        """Comprueba los datos y el estado del escenario de la prueba."""
        await calcular_inversa(vista)
        ejecutar = Mock()
        monkeypatch.setattr(ui, "run_javascript", ejecutar)
        boton = next(elemento for elemento in cliente.elements.values()
                     if isinstance(elemento, ui.button) and elemento._props.get("label") == "Copiar A⁻¹")
        manejador = next(iter(boton._event_listeners.values())).handler
        manejador(None)
        assert "1/2" in ejecutar.call_args.args[0]
        assert "1/3" in ejecutar.call_args.args[0]
    asyncio.run(construir_pagina(monkeypatch, "inversa", comprobar))
