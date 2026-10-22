"""Disposición, tokens y accesibilidad de la navegación contextual."""
from pathlib import Path
import re

RUTA_CSS = Path("src/frontend/recursos/css/vistas_navegacion.css")


def leer_estilos_navegacion() -> str:
    """Lee la hoja de estilos de navegación para sus comprobaciones estáticas."""
    return RUTA_CSS.read_text(encoding="utf-8")


def test_navegacion_cuadricula_de_una_fila():
    """La cabecera centra una cuadrícula de una sola fila con altura acotada."""
    css = leer_estilos_navegacion()
    assert ".navegacion-cabecera" in css
    cabecera = re.search(r'\.navegacion-cabecera\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: flex;" in cabecera
    assert "align-items: center;" in cabecera
    assert "justify-content: center;" in cabecera
    assert "background: transparent" in cabecera or "background-color: transparent" in cabecera
    assert "color: var(--text-main)" in cabecera
    assert re.search(r'height:\s*(?:6[4-9]|7[0-2])px', cabecera) or re.search(r'min-height:\s*(?:6[4-9]|7[0-2])px', cabecera)
    pastilla = re.search(r'\.navegacion-capsula\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: grid;" in pastilla
    assert "grid-template-columns: auto minmax(0, 1fr) auto;" in pastilla or "grid-template-columns: auto minmax(0,1fr) auto;" in pastilla
    assert "grid-template-rows: 1fr;" in pastilla
    assert re.search(r'height:\s*(?:6[4-9]|7[0-2])px', pastilla) or re.search(r'min-height:\s*(?:6[4-9]|7[0-2])px', pastilla)


def test_solo_la_lista_permite_desplazamiento():
    """La lista desplaza etiquetas completas y conserva indicadores de continuidad."""
    css = leer_estilos_navegacion()
    centro = re.search(r'\.navegacion-centro\s*\{(.*?)\}', css, re.DOTALL).group(1)
    lista = re.search(r'\.navegacion-elementos\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "overflow: hidden;" in centro
    assert "min-width: 0;" in centro
    assert "overflow-x: auto;" in lista
    assert "scrollbar-width: thin;" in lista
    assert "overscroll-behavior-x: contain;" in lista
    assert "data-opciones-antes" in css
    assert "data-opciones-despues" in css


def test_navegacion_inicio_y_tema_no_se_encogen():
    """Las acciones laterales conservan su espacio cuando falta anchura."""
    css = leer_estilos_navegacion()
    coincidencia = re.search(r'([^\{\}]*navegacion-inicio[^\{\}]*)\{(.*?)\}', css, re.DOTALL)
    assert coincidencia, "No se encontró regla para .navegacion-inicio"
    assert "flex-shrink: 0;" in coincidencia.group(2)
    assert "tema-boton-selector" in coincidencia.group(1) or "navegacion-tema" in coincidencia.group(1)


def test_navegacion_muestra_etiquetas_completas_sin_recortes():
    """El móvil conserva el texto completo y un foco visible dentro de la lista."""
    css = leer_estilos_navegacion()
    etiqueta = re.search(r'\.navegacion-etiqueta-completa\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: inline;" in etiqueta
    assert "white-space: nowrap;" in etiqueta
    assert "text-overflow" not in css
    assert "navegacion-etiqueta-breve" not in css
    assert ".navegacion-elemento:focus-visible" in css
    assert "outline: 2px solid var(--accent);" in css


def test_navegacion_colores_definidos_por_tokens():
    """La navegación evita colores literales fuera del sistema de tokens."""
    css = leer_estilos_navegacion()
    hexadecimales = re.findall(r'#[0-9a-fA-F]{3,8}\b', css)
    assert hexadecimales == [], f"Colores hexadecimales literales en navegación: {hexadecimales}"
    coincidencias_rgb = re.findall(r'rgba?\([^\)]*\)', css)
    for rgb in coincidencias_rgb:
        assert "var(" in rgb, f"Color RGB literal sin token en navegación: {rgb}"


def test_navegacion_respeta_movimiento_reducido_y_curvas():
    """La preferencia de movimiento reducido anula transiciones y transformaciones."""
    css = leer_estilos_navegacion()
    assert not re.search(r'transition:[^;]*\bease-in\b', css)
    assert "@media (prefers-reduced-motion: reduce)" in css
    coincidencia = re.search(r'@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)\n\}', css, re.DOTALL)
    assert coincidencia, "No se encontró bloque de movimiento reducido en navegación"
    movimiento_reducido = coincidencia.group(1)
    assert "transform: none !important;" in movimiento_reducido
    assert "transition: none !important;" in movimiento_reducido
    assert ".navegacion-accion" in movimiento_reducido
    assert ".navegacion-capsula" in movimiento_reducido
