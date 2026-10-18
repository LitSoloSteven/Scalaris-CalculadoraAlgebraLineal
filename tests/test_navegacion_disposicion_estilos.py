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


def test_navegacion_zona_central_permite_desplazamiento():
    """La zona central puede encogerse y desplazarse sin barra visible."""
    css = leer_estilos_navegacion()
    assert ".navegacion-centro" in css
    centro = re.search(r'\.navegacion-centro\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "min-width: 0;" in centro
    assert "overflow-x: auto;" in centro
    assert "scrollbar-width: none;" in centro
    assert "mask-image:" in centro
    assert ".navegacion-centro::-webkit-scrollbar" in css
    barra_desplazamiento = re.search(r'\.navegacion-centro::-webkit-scrollbar\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: none;" in barra_desplazamiento


def test_navegacion_inicio_y_tema_no_se_encogen():
    """Las acciones laterales conservan su espacio cuando falta anchura."""
    css = leer_estilos_navegacion()
    coincidencia = re.search(r'([^\{\}]*navegacion-inicio[^\{\}]*)\{(.*?)\}', css, re.DOTALL)
    assert coincidencia, "No se encontró regla para .navegacion-inicio"
    assert "flex-shrink: 0;" in coincidencia.group(2)
    assert "tema-boton-selector" in coincidencia.group(1) or "navegacion-tema" in coincidencia.group(1)


def test_navegacion_muestra_una_sola_etiqueta():
    """Cada anchura muestra una única variante de la etiqueta."""
    css = leer_estilos_navegacion()
    completa_predeterminada = re.search(r'\n\.navegacion-etiqueta-completa\s*\{(.*?)\}', css, re.DOTALL).group(1)
    corta_predeterminada = re.search(r'\n\.navegacion-etiqueta-breve\s*\{(.*?)\}', css, re.DOTALL).group(1)
    assert "display: none;" in completa_predeterminada
    assert "display: none;" in corta_predeterminada
    consulta_700 = re.search(r'@container\s+barra-navegacion\s*\(\s*min-width:\s*700px\s*\)\s*\{(.*?)\n\}', css, re.DOTALL).group(1)
    assert ".navegacion-etiqueta-breve" in consulta_700
    assert "display: inline;" in consulta_700
    assert ".navegacion-etiqueta-completa" in consulta_700
    assert "display: none;" in consulta_700
    consulta_960 = re.search(r'@container\s+barra-navegacion\s*\(\s*min-width:\s*960px\s*\)\s*\{(.*?)\n\}', css, re.DOTALL).group(1)
    assert ".navegacion-etiqueta-completa" in consulta_960
    assert "display: inline;" in consulta_960
    assert ".navegacion-etiqueta-breve" in consulta_960
    assert "display: none;" in consulta_960


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
