"""Comportamiento de los nombres permanentes en la captura matricial real."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.componentes.captura_matrices import PanelCapturaMatrices
from tests.comun_construccion_vistas import construir_pagina


def test_panel_inicia_con_dos_matrices_y_reserva_sus_nombres():
    """A y B existen incluso antes del montaje; el siguiente nombre es C."""
    panel = PanelCapturaMatrices()
    assert set(panel.matrices) == {"A", "B"}
    assert panel.obtener_siguiente_nombre_disponible() == "C"


def test_proteccion_visual_y_manejador_con_matrices_adicionales(monkeypatch):
    """Eliminar A/B no modifica entradas ni notifica; C puede eliminarse y reutilizarse."""
    async def comprobar(vista, cliente):
        """Ejercita botones y manejadores sobre cuatro matrices montadas."""
        panel = vista.panel_captura_matrices
        panel.agregar_matriz()
        panel.agregar_matriz()
        panel.matrices["A"]["entradas"][0][0].set_value("1/1001")
        panel.matrices["B"]["entradas"][0][0].set_value("-7/9")
        antes = panel.obtener_datos_crudos()
        avisos = []
        panel.al_cambiar_datos = lambda: avisos.append(True)
        for nombre in ("A", "B"):
            boton = next(elemento for elemento in cliente.elements.values()
                         if elemento._props.get("aria-label") == f"Eliminar matriz {nombre}")
            assert boton._props["disable"]
            panel.eliminar_matriz(nombre)
        assert panel.obtener_datos_crudos() == antes
        assert avisos == []
        panel.eliminar_matriz("C")
        assert set(panel.matrices) == {"A", "B", "D"}
        assert panel.obtener_siguiente_nombre_disponible() == "C"
        assert avisos == [True]
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


@pytest.mark.parametrize("carga", [{}, {"C": [["1/1001", "-2/3"]]}, {"B": [["9"]], "Z": [["7"]]}])
def test_carga_y_reconstruccion_completan_solo_nombres_ausentes(monkeypatch, carga):
    """Restaurar colecciones parciales preserva sus nombres, dimensiones y datos."""
    async def comprobar(vista, cliente):
        """Reconstruye la carga parcial sin alterar registros presentes."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos(carga)
        panel.construir(panel.contenedor)
        panel.renderizar_todas()
        assert set(panel.matrices) == set(carga) | {"A", "B"}
        for nombre, datos in carga.items():
            assert panel.obtener_datos_crudos()[nombre]["datos"] == datos
        assert all(panel.matrices[nombre]["filas"] == 3 for nombre in {"A", "B"} - set(carga))
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_cargar_antes_del_montaje_conserva_cache_y_dimensiones(monkeypatch):
    """El montaje de una captura restaurada no reemplaza A ni renombra C."""
    async def comprobar(vista, cliente):
        """Monta un panel restaurado sin entradas de interfaz anteriores."""
        panel = PanelCapturaMatrices()
        panel.cargar_datos({"A": [["-1/3"]], "C": [["2", "7"]]})
        panel.construir(ui.column())
        assert panel.obtener_datos_crudos()["A"]["datos"] == [["-1/3"]]
        assert panel.obtener_datos_crudos()["C"]["datos"] == [["2", "7"]]
        assert set(panel.matrices) == {"A", "B", "C"}
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_limpiar_vacia_datos_sin_perder_matrices_ni_dimensiones(monkeypatch):
    """La accion real conserva A/B/C y retira expresion, resultado y contexto."""
    async def comprobar(vista, cliente):
        """Limpia una captura rectangular y un resultado exacto vigente."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos({"A": [["1/3", "7"]], "B": [["5"]], "C": [["9"], ["8"]]})
        vista.entrada_expresion.set_value("B+B")
        await vista.evaluar_expresion(ui.button("Evaluar prueba"))
        assert vista.ultimo_resultado["estado"] == "EXITO"
        vista.limpiar_todo()
        assert vista.entrada_expresion.value == ""
        assert vista.ultimo_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert {nombre: datos["datos"] for nombre, datos in panel.obtener_datos_crudos().items()} == {
            "A": [["", ""]], "B": [[""]], "C": [[""], [""]],
        }
        panel.renderizar_todas()
        assert panel.obtener_datos_crudos()["A"]["datos"] == [["", ""]]
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))
