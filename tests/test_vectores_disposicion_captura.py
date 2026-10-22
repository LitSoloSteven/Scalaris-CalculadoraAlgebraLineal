"""Conservacion de capturas y controles al reorganizar tarjetas vectoriales."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("dimension", [1, 3, 8])
@pytest.mark.parametrize("orientacion", ["fila", "columna"])
def test_reconstruccion_conserva_valores_y_orientacion(monkeypatch, dimension, orientacion):
    """Orientar y reconstruir no recorta componentes ni sustituye numeros largos."""
    async def comprobar(vista, cliente):
        """Carga ambas tarjetas y recorre los cambios reales de orientacion."""
        panel = vista.panel_suma_resta
        valores = ["123456789012345678901234567890/1001"] * dimension
        panel.cargar_datos({"u": valores, "v": ["-2/3"] * dimension}, orientacion)
        cabecera = panel.contenedor_cabecera
        for nombre in ("u", "v"):
            panel.alternar_orientacion(nombre)
            panel.alternar_orientacion(nombre)
        panel.renderizar_todos_vectores()
        assert panel.contenedor_cabecera is cabecera and not cabecera.is_deleted
        assert panel.dimension == dimension
        assert vista._capturar()["u"]["datos"] == valores
        for nombre, vector in panel.vectores.items():
            entradas = [elemento for elemento in vector["contenedor"].descendants() if isinstance(elemento, ui.input)]
            assert len(entradas) == dimension
            assert vector["orientacion"] == orientacion
            assert [entrada.value for entrada in entradas] == (["-2/3"] * dimension if nombre == "v" else valores)
    asyncio.run(construir_pagina(monkeypatch, "vectores", comprobar))


def test_cabecera_permanece_antes_de_tarjetas_al_agregar_y_eliminar(monkeypatch):
    """Los controles de familia permanecen montados mientras cambia la coleccion."""
    async def comprobar(vista, cliente):
        """Agrega un vector a combinacion lineal y conserva el objetivo y los controles."""
        vista.pestanas.set_value("combinacion_lineal")
        panel = vista.panel_combinacion
        panel.cargar_datos({"b": ["2", "4"], "v_1": ["1", "2"]})
        cabecera = panel.contenedor_cabecera
        padre = cabecera.parent_slot
        assert padre is panel.contenedor.parent_slot
        assert padre.children.index(cabecera) < padre.children.index(panel.contenedor)
        panel.agregar_vector()
        panel.eliminar_vector("v_2")
        assert not cabecera.is_deleted
        assert panel.boton_aumentar_dimension in list(cabecera.descendants())
        assert vista._capturar()["b"]["datos"] == ["2", "4"]
        await vista.calcular()
        assert vista.resultado_actual["estado"] == "UNICA"
        assert vista.resultado_actual["coeficientes_texto"] == ["2"]
    asyncio.run(construir_pagina(monkeypatch, "vectores", comprobar))
