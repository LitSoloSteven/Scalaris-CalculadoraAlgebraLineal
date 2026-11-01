"""Montaje, retirada y recuperación de las gráficas de transformaciones."""
import asyncio
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.vistas.operaciones_matrices import grafica_aplicacion_transformacion as montaje
from src.frontend.vistas.operaciones_matrices._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from tests.comun_construccion_vistas import construir_pagina


def _graficas(vista):
    return [elemento for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.plotly)]


def _etiquetas(vista):
    return [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]


@pytest.mark.parametrize("cambio", ["vector", "matriz", "dimension", "modo", "tipo", "limpiar", "desmontar"])
def test_editar_o_desmontar_retira_todas_las_figuras(monkeypatch, cambio):
    """Las figuras pertenecen al resultado vigente y no quedan retenidas por la vista."""
    async def comprobar(vista, cliente):
        """Monta una aplicación real y elimina el resultado mediante cada ruta de captura."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        await vista._analizar(vista.boton_calcular)
        anteriores = _graficas(vista)
        assert len(anteriores) == 1
        acciones = {
            "vector": lambda: vista.entradas_vector_original[0].set_value("7"),
            "matriz": lambda: vista.entradas_coeficientes[0][0].set_value("7"),
            "dimension": lambda: vista._aplicar_dimension("filas", 3),
            "modo": lambda: vista.selector_modo.set_value(textos.MODO_ANALISIS),
            "tipo": lambda: vista.selector_tipo_objeto.set_value("punto"),
            "limpiar": vista.limpiar_todo,
            "desmontar": vista.contenedor_resultados.delete,
        }
        acciones[cambio]()
        assert all(grafica.is_deleted and grafica.id not in cliente.elements for grafica in anteriores)
        if cambio != "desmontar":
            assert not _graficas(vista) and vista.ultimo_resultado is None
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_fallo_de_segunda_escena_retira_el_montaje_parcial(monkeypatch):
    """Un fallo gráfico no deja solo el dominio de una transformación rectangular."""
    async def comprobar(vista, cliente):
        """Falla después de montar el primer espacio y exige conservar solo los valores exactos."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        vista._aplicar_dimension("filas", 3)
        montar = montaje._montar_escena

        def montar_o_fallar(escena):
            """Monta el dominio real y simula una avería al recibir el codominio."""
            if escena["titulo"].startswith("Codominio"):
                raise RuntimeError("fallo de codominio")
            montar(escena)

        monkeypatch.setattr(montaje, "_montar_escena", montar_o_fallar)
        await vista._analizar(vista.boton_calcular)
        assert not _graficas(vista)
        assert textos.GRAFICA_ERROR in _etiquetas(vista)
        assert textos.COORDENADAS_EXACTAS in _etiquetas(vista)
        assert not any(isinstance(elemento, ui.plotly) for elemento in cliente.elements.values())
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_montaje_rectangular_y_sincronizacion_tema_bajo_demanda(monkeypatch):
    """Dos espacios usan el recurso común de tema y el redimensionado nativo de NiceGUI."""
    async def comprobar(vista, cliente):
        """Inspecciona las opciones y accesibilidad de los elementos Plotly reales."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        vista._aplicar_dimension("filas", 3)
        await vista._analizar(vista.boton_calcular)
        graficas = _graficas(vista)
        assert len(graficas) == 2
        assert "Dominio: R^2" in _etiquetas(vista) and "Codominio: R^3" in _etiquetas(vista)
        assert textos.GRAFICA_EJES_2D in _etiquetas(vista) and textos.GRAFICA_EJES_3D in _etiquetas(vista)
        for grafica in graficas:
            assert grafica._props["role"] == "img" and grafica._props["aria-label"]
            assert grafica.figure["config"]["responsive"] is True
            assert grafica.figure["config"]["displayModeBar"] is False
            assert any("tema_graficos.js?v=" in evento.js_handler for evento in grafica._event_listeners.values())
        assert textos.GRAFICA_APROXIMADA in _etiquetas(vista)
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


@pytest.mark.parametrize("fallo", ["dimension", "desborde", "renderizado"])
def test_omitir_o_fallar_grafica_no_oculta_coordenadas(monkeypatch, fallo):
    """El resultado exacto permanece disponible cuando la escena no puede montarse."""
    async def comprobar(vista, cliente):
        """Ejercita límites reales del dominio y una avería de la biblioteca gráfica."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        if fallo == "dimension":
            vista._aplicar_dimension("filas", 4)
        elif fallo == "desborde":
            vista.entradas_coeficientes[0][0].set_value("9" * 256)
            vista.entradas_vector_original[0].set_value("9" * 256)
        else:
            monkeypatch.setattr(montaje, "preparar_escenas_aplicacion", Mock(side_effect=RuntimeError("fallo gráfico")))
        await vista._analizar(vista.boton_calcular)
        assert vista.ultimo_resultado["estado"] == "EXITO"
        assert textos.COORDENADAS_EXACTAS in _etiquetas(vista)
        assert not _graficas(vista)
        assert not vista.boton_calcular._props.get("loading", False)
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
