"""Tokens de movimiento, celdas anchas, sugerencias y accesibilidad."""
from pathlib import Path
import re
import pytest
from tests.comun_javascript import leer_captura_cliente, leer_interacciones_cliente
from tests.comun_estilos import bloque_css


def test_tokens_movimiento_y_entradas_resistentes():
    """Conserva las restricciones de contenedores, celdas y movimiento."""
    from tests.comun import leer_css_completo, RAIZ
    contenido = leer_css_completo()
    _comprobar_contenedores_y_celdas(contenido)
    _comprobar_curvas_y_entradas(contenido)
    _comprobar_movimiento_reducido_y_sugerencias(contenido, RAIZ)


def _comprobar_contenedores_y_celdas(contenido):
    assert contenido.count("container-type: inline-size") == 4
    assert "100vh" not in contenido
    assert contenido.count("--fab-reserve:") >= 4

    assert contenido.count("--cell-w:") >= 4
    assert ".cuadricula-celda {" in contenido
    assert ".cuadricula-celda-compacta {" in contenido

    assert "@keyframes keyPulse" not in contenido
    assert ".key-pulse" not in contenido
    assert ".cuadricula-resaltado-cruzado {" in contenido



def _comprobar_curvas_y_entradas(contenido):
    assert "transition: transform var(--dur-state) var(--ease-std), opacity var(--dur-state) var(--ease-std) !important;" in contenido
    assert "var(--ease-elastic)" not in contenido.split(".pestanas-controles .q-tab__indicator")[1].split("}")[0]

    css_boton_icono = contenido.split(".boton-icono {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in css_boton_icono
    assert "var(--ease-std)" in css_boton_icono

    css_boton_calculadora = contenido.split(".calculadora-boton {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in css_boton_calculadora
    assert "var(--ease-std)" in css_boton_calculadora

    css_logo = contenido.split(".marca-enlace-logotipo {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in css_logo
    assert "var(--ease-std)" in css_logo

    css_deslizamiento_vertical = contenido.split(".movimiento-entrada {")[1].split("}")[0]
    assert "var(--dur-panel)" in css_deslizamiento_vertical
    assert "var(--ease-std)" in css_deslizamiento_vertical

    css_rebote = contenido.split(".movimiento-rebote {")[1].split("}")[0]
    assert "var(--dur-panel)" in css_rebote
    assert "var(--ease-std)" in css_rebote

    css_compresion = contenido.split(".movimiento-compresion {")[1].split("}")[0]
    assert "var(--dur-panel)" in css_compresion
    assert "var(--ease-std)" in css_compresion



def _comprobar_movimiento_reducido_y_sugerencias(contenido, raiz):
    css_celda_inversa = contenido.split(".inversa-tabla th,")[1].split(".inversa-tabla thead th {")[0]
    assert "max-width: 16ch" not in css_celda_inversa
    assert "text-overflow: ellipsis" not in css_celda_inversa

    parte_movimiento_reducido = (raiz / "src" / "frontend" / "recursos" / "css" / "movimiento.css").read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in parte_movimiento_reducido
    assert ".escritura-cursor" in parte_movimiento_reducido
    assert ".glosa-indicador-escritura span" in parte_movimiento_reducido
    assert ".movimiento-sacudida" in parte_movimiento_reducido
    assert ".movimiento-compresion" in parte_movimiento_reducido
    assert ".movimiento-entrada" in parte_movimiento_reducido
    assert "animation: none !important;" in parte_movimiento_reducido
    assert "transition-duration: var(--dur-reduced) !important;" in parte_movimiento_reducido

    assert ".glosa-sugerencias {" in contenido
    assert ".glosa-sugerencias-en-linea {" in contenido
    assert ".glosa-sugerencia {" in contenido
    assert ".glosa-sugerencia-en-linea {" in contenido
    assert ".glosa-seguimientos {" in contenido
    assert ".glosa-seguimiento {" in contenido


def test_cliente_delega_ayuda_y_no_anima_teclado():
    """La ayuda de entradas largas se delega y la recolección conserva su curva."""
    javascript_aplicacion = leer_interacciones_cliente()
    recoleccion_js = Path("src/frontend/recursos/js/recoleccion_basura.js").read_text(encoding="utf-8")
    assert "key-pulse" not in javascript_aplicacion
    assert "scrollWidth > objetivo.clientWidth" in javascript_aplicacion
    assert "objetivo.title = objetivo.value" in javascript_aplicacion
    assert "movimiento.duracion('--dur-panel')" in recoleccion_js
    assert "movimiento.curva()" in recoleccion_js


def test_cliente_resaltado_cruzado_sin_desenfoque():
    """Las cuadrículas resaltan celdas sin cambiar fondo ni aplicar desenfoque."""
    cuadricula_ecuaciones = leer_captura_cliente("captura_ecuaciones.js")
    assert "cuadricula-resaltado-cruzado" in cuadricula_ecuaciones
    assert "filter: blur" not in cuadricula_ecuaciones
    assert "style.background =" not in cuadricula_ecuaciones

    captura_matrices = leer_captura_cliente("captura_matrices.js")
    assert "cuadricula-resaltado-cruzado" in captura_matrices
    assert "style.background =" not in captura_matrices

    captura_vectores = leer_captura_cliente("captura_vectores.js")
    assert "cuadricula-resaltado-cruzado" in captura_vectores
    assert "filter: blur" not in captura_vectores
    assert "style.background =" not in captura_vectores

    matriz_cuadrada = Path("src/frontend/recursos/js/matriz_cuadrada.js").read_text(encoding="utf-8")
    assert "filter: blur" not in matriz_cuadrada


def test_componentes_celdas_resistentes_y_animaciones():
    """Las cuadrículas usan clases de celdas con tamaño adaptable."""
    python_matrices = Path("src/frontend/componentes/captura_matrices.py").read_text(encoding="utf-8")
    assert "filter: 'blur" not in python_matrices
    assert "cuadricula-celda" in python_matrices
    assert "w-20" not in python_matrices

    python_ecuaciones = Path("src/frontend/componentes/cuadricula_ecuaciones.py").read_text(encoding="utf-8")
    assert "cuadricula-celda" in python_ecuaciones
    assert "w-20" not in python_ecuaciones

    python_vectores = Path("src/frontend/componentes/captura_vectores.py").read_text(encoding="utf-8")
    assert "cuadricula-celda" in python_vectores
    assert "w-20" not in python_vectores

    python_matriz_cuadrada = Path("src/frontend/componentes/panel_matriz_cuadrada.py").read_text(encoding="utf-8")
    assert "CELL_PX" not in python_matriz_cuadrada
    assert "cuadricula-celda" in python_matriz_cuadrada
    assert "cuadricula-celda-compacta" in python_matriz_cuadrada


def test_vistas_sanean_resultados_y_contienen_contenido_ancho():
    """Las vistas contienen fórmulas anchas y escapan texto del resultado."""
    mixin_numerico = Path("src/frontend/vistas/sistemas_numericos/mixin_interaccion.py").read_text(encoding="utf-8")
    assert "movimiento-sacudida" not in mixin_numerico

    resultados_lineales = Path("src/frontend/vistas/sistemas_lineales/mixin_resultados.py").read_text(encoding="utf-8")
    css_sesion = Path('src/frontend/recursos/css/vistas_sesion_matricial.css').read_text(encoding='utf-8')
    assert "overflow-wrap: anywhere;" in bloque_css(css_sesion, '.sesion-numero') and "sesion-numero" in resultados_lineales
    assert "min-w-0 max-w-full" in resultados_lineales

    resultados_vectoriales = Path("src/frontend/vistas/operaciones_vectores/mixin_resultados.py").read_text(encoding="utf-8")
    assert "matematicas-desplazamiento" in resultados_vectoriales
    assert "html.escape(coeficientes)" in resultados_vectoriales
    assert "html.escape(solucion)" in resultados_vectoriales
