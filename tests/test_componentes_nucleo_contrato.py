"""APIs canónicas y ausencia de alias en componentes y navegación."""
from dataclasses import fields

import pytest

from src.frontend import navegacion
from src.frontend.componentes.calculadora import PanelCalculadora
from src.frontend.componentes.cuadricula_ecuaciones import CuadriculaEcuaciones
from src.frontend.componentes.captura_matrices import PanelCapturaMatrices
from src.frontend.componentes.captura_vectores import PanelCapturaVectores
from src.frontend.componentes.panel_matriz_cuadrada import PanelMatrizCuadrada
from tests.comun import RAIZ


@pytest.mark.parametrize("modelo,esperados", [
    (navegacion.Pilar, {"identificador", "nombre", "icono", "nombre_corto", "prefijo"}),
    (navegacion.Herramienta, {
        "identificador", "nombre", "descriptor", "ruta", "identificador_pilar", "icono",
        "titulo_pagina", "ejemplo_latex", "habilitada",
    }),
    (navegacion.ElementoNavegacion, {
        "clave", "etiqueta", "etiqueta_corta", "descriptor", "icono", "ruta", "consulta",
        "identificador_herramienta",
    }),
])
def test_modelos_de_navegacion_tienen_un_solo_contrato(modelo, esperados):
    """Los productores y consumidores comparten exactamente los campos españoles."""
    assert {campo.name for campo in fields(modelo)} == esperados


@pytest.mark.parametrize("constructor,actual,anteriores", [
    (PanelCalculadora, "construir", ("build", "inject_scripts")),
    (CuadriculaEcuaciones, "construir_contenedor_cuadricula",
     ("build_grid_container", "adjust_size", "is_strictly_empty", "clear", "on_data_change")),
    (PanelCapturaMatrices, "construir",
     ("build", "on_invert", "on_data_change", "get_next_available_name", "adjust_size")),
    (lambda: PanelCapturaVectores("prueba"), "construir",
     ("build", "vectors", "dim", "container", "load_data", "render_vector_grid")),
    (PanelMatrizCuadrada, "construir_contenedor",
     ("build_container", "cells", "rows_ui", "paste_from_clipboard", "is_empty", "clear", "obtener_matriz")),
])
def test_captura_expone_metodos_reales_y_retira_los_alias(constructor, actual, anteriores):
    """Cada componente expone su constructor vigente sin compatibilidad inglesa."""
    componente = constructor()
    assert callable(getattr(componente, actual))
    assert callable(componente.inyectar_recursos_cliente)
    assert not any(hasattr(componente, anterior) for anterior in anteriores)


@pytest.mark.parametrize("retirado", [
    "app.py", "routes.py", "flags.py", "helpers.py", "navigation",
    "componentes/calculator.py", "componentes/equation_grid.py",
    "componentes/matrix_capture.py", "componentes/vector_capture.py",
    "componentes/square_matrix_panel.py", "componentes/navbar.py",
    "componentes/icons.py", "componentes/handoff.py", "componentes/app_shell.py",
    "assets/js/square_matrix.js",
])
def test_fuentes_retiradas_no_constituyen_un_segundo_arbol(retirado):
    """Los módulos anteriores dejan de existir como fuentes activas."""
    assert not (RAIZ / "src/frontend" / retirado).exists()


def test_navegacion_retira_los_nombres_publicados_anteriores():
    """El registro publica exclusivamente sus clases y consultas canónicas."""
    anteriores = ("Pillar", "Tool", "NavItem", "nav_items", "tool_by_id", "route_of", "HUB_ROUTE")
    assert not any(hasattr(navegacion, nombre) for nombre in anteriores)


@pytest.mark.parametrize("alias", ["algebra-lineal", "geometria", "utilidades-numericas"])
def test_identificadores_alternativos_de_pilares_no_se_aceptan(alias):
    """Cada pilar se consulta exclusivamente por su identificador canónico."""
    assert navegacion.elementos_navegacion(alias) == ()


def test_catalogo_conserva_los_simbolos_matematicos_originales():
    """La traducción de identificadores Python no altera fórmulas ni descriptores."""
    assert navegacion.herramienta_por_identificador("vectores").ejemplo_latex == (
        r"c_1\mathbf{v}_1 + c_2\mathbf{v}_2 = \mathbf{b}"
    )
    assert navegacion.herramienta_por_identificador("visualizador").ejemplo_latex == (
        r"\mathbf{x} = \mathbf{p} + t\,\mathbf{d}"
    )
    assert navegacion.ESCENAS_VISUALIZADOR[1][3] == "Suma y escalamiento de u y v"
