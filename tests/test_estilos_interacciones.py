"""Tokens de movimiento, celdas anchas, sugerencias y accesibilidad."""
from pathlib import Path
import re
import pytest
from tests.comun_javascript import leer_captura_cliente, leer_interacciones_cliente


def test_tokens_movimiento_y_entradas_resistentes():
    """Conserva las restricciones de contenedores, celdas y movimiento."""
    from tests.comun import leer_css_completo, RAIZ
    content = leer_css_completo()
    _comprobar_contenedores_y_celdas(content)
    _comprobar_curvas_y_entradas(content)
    _comprobar_movimiento_reducido_y_sugerencias(content, RAIZ)


def _comprobar_contenedores_y_celdas(content):
    assert content.count("container-type: inline-size") == 3
    assert "100vh" not in content
    assert content.count("--fab-reserve:") >= 4

    assert content.count("--cell-w:") >= 4
    assert ".grid-cell {" in content
    assert ".grid-cell-compact {" in content

    assert "@keyframes keyPulse" not in content
    assert ".key-pulse" not in content
    assert ".cuadricula-resaltado-cruzado {" in content



def _comprobar_curvas_y_entradas(content):
    assert "transition: transform var(--dur-med) var(--ease-std), opacity var(--dur-med) var(--ease-std) !important;" in content
    assert "var(--ease-elastic)" not in content.split(".neo-tabs .q-tab__indicator")[1].split("}")[0]

    icon_btn_css = content.split(".btn-neo-icon {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in icon_btn_css
    assert "var(--ease-std)" in icon_btn_css

    calc_btn_css = content.split(".btn-neo-calc {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in calc_btn_css
    assert "var(--ease-std)" in calc_btn_css

    logo_css = content.split(".brand-logo-link {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in logo_css
    assert "var(--ease-std)" in logo_css

    slide_up_css = content.split(".animate-slide-up {")[1].split("}")[0]
    assert "var(--dur-med)" in slide_up_css
    assert "var(--ease-std)" in slide_up_css

    slide_bounce_css = content.split(".animate-slide-bounce {")[1].split("}")[0]
    assert "var(--dur-med)" in slide_bounce_css
    assert "var(--ease-std)" in slide_bounce_css

    squash_css = content.split(".squash-bounce {")[1].split("}")[0]
    assert "var(--dur-med)" in squash_css
    assert "var(--ease-std)" in squash_css



def _comprobar_movimiento_reducido_y_sugerencias(content, raiz):
    inv_cell_css = content.split(".inv-table th,")[1].split(".inv-table thead th {")[0]
    assert "max-width: 16ch" not in inv_cell_css
    assert "text-overflow: ellipsis" not in inv_cell_css

    reduced_part = (raiz / "src" / "frontend" / "assets" / "css" / "movimiento.css").read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in reduced_part
    assert ".tw-cursor" in reduced_part
    assert ".glosa-typing-indicator span" in reduced_part
    assert ".animate-shake" in reduced_part
    assert ".squash-bounce" in reduced_part
    assert ".animate-slide-up" in reduced_part
    assert "animation: none !important;" in reduced_part
    assert "transition-duration: 120ms !important;" in reduced_part

    assert ".glosa-chips {" in content
    assert ".glosa-chips-inline {" in content
    assert ".glosa-chip {" in content
    assert ".glosa-chip-inline {" in content
    assert ".glosa-followups {" in content
    assert ".glosa-followup {" in content


def test_cliente_delega_ayuda_y_no_anima_teclado():
    """La ayuda de entradas largas se delega y la recolección conserva su curva."""
    app_js = leer_interacciones_cliente()
    recoleccion_js = Path("src/frontend/assets/js/recoleccion_basura.js").read_text(encoding="utf-8")
    assert "key-pulse" not in app_js
    assert "scrollWidth > objetivo.clientWidth" in app_js
    assert "objetivo.title = objetivo.value" in app_js
    assert "transform 160ms cubic-bezier(0.32, 0.72, 0, 1), opacity 160ms cubic-bezier(0.32, 0.72, 0, 1)" in recoleccion_js


def test_cliente_resaltado_cruzado_sin_desenfoque():
    """Las cuadrículas resaltan celdas sin cambiar fondo ni aplicar desenfoque."""
    eq_grid = leer_captura_cliente("captura_ecuaciones.js")
    assert "cuadricula-resaltado-cruzado" in eq_grid
    assert "filter: blur" not in eq_grid
    assert "style.background =" not in eq_grid

    mat_cap = leer_captura_cliente("captura_matrices.js")
    assert "cuadricula-resaltado-cruzado" in mat_cap
    assert "style.background =" not in mat_cap

    vec_cap = leer_captura_cliente("captura_vectores.js")
    assert "cuadricula-resaltado-cruzado" in vec_cap
    assert "filter: blur" not in vec_cap
    assert "style.background =" not in vec_cap

    sq_mat = Path("src/frontend/assets/js/square_matrix.js").read_text(encoding="utf-8")
    assert "filter: blur" not in sq_mat


def test_componentes_celdas_resistentes_y_animaciones():
    """Las cuadrículas usan clases de celdas con tamaño adaptable."""
    mat_py = Path("src/frontend/componentes/matrix_capture.py").read_text(encoding="utf-8")
    assert "filter: 'blur" not in mat_py
    assert "grid-cell" in mat_py
    assert "w-20" not in mat_py

    eq_py = Path("src/frontend/componentes/equation_grid.py").read_text(encoding="utf-8")
    assert "grid-cell" in eq_py
    assert "w-20" not in eq_py

    vec_py = Path("src/frontend/componentes/vector_capture.py").read_text(encoding="utf-8")
    assert "grid-cell" in vec_py
    assert "w-20" not in vec_py

    sq_py = Path("src/frontend/componentes/square_matrix_panel.py").read_text(encoding="utf-8")
    assert "CELL_PX" not in sq_py
    assert "grid-cell" in sq_py
    assert "grid-cell-compact" in sq_py


def test_vistas_sanean_resultados_y_contienen_contenido_ancho():
    """Las vistas contienen fórmulas anchas y escapan texto del resultado."""
    num_mixin = Path("src/frontend/vistas/numeric_systems/interaction_mixin.py").read_text(encoding="utf-8")
    assert "animate-shake" not in num_mixin

    lin_res = Path("src/frontend/vistas/linear_systems/results_mixin.py").read_text(encoding="utf-8")
    assert "overflow-wrap: anywhere;" in lin_res
    assert "min-w-0 max-w-full" in lin_res

    vec_res = Path("src/frontend/vistas/operaciones_vectores/mixin_resultados.py").read_text(encoding="utf-8")
    assert "math-scroll-container" in vec_res
    assert "html.escape(coeficientes)" in vec_res
    assert "html.escape(solucion)" in vec_res
