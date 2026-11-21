"""Contratos del selector de símbolos sin botón visible y diálogo con cabecera fija."""
import re

from nicegui import ui

from src.frontend.componentes.campo_funcion_real import crear_campo_funcion
from src.frontend.componentes.aplicacion.base.simbolos import habilitar_simbolos
from tests.comun import RAIZ


def _bloque_css(texto_css: str, selector: str) -> str:
    patron = re.escape(selector) + r"\s*\{([^}]*)\}"
    coincidencia = re.search(patron, texto_css, re.DOTALL)
    assert coincidencia is not None, f"No se encontró la regla CSS '{selector}'."
    return coincidencia.group(1)


def test_habilitar_simbolos_declara_atajos_sin_montar_boton_visible():
    """El ayudante configura atributos de acceso sin agregar botón en el campo."""
    with ui.column() as contenedor:
        try:
            campo = ui.input("Expresión")
            habilitar_simbolos(campo, "matriz", atajos="Control+Shift+2")
            assert campo._props.get("data-simbolos") == "matriz"
            assert campo._props.get("aria-keyshortcuts") == "Control+Shift+Space Control+Shift+2"
            assert "append" not in campo.slots
            plantillas = "".join(slot.template or "" for slot in campo.slots.values())
            assert "simbolos-boton" not in plantillas
            assert "data-campo-simbolos" not in plantillas
        finally:
            contenedor.delete()


def test_crear_campo_funcion_conserva_aviso_teclado_sin_boton_visible():
    """El campo compartido conserva la indicación de teclado y omite botones."""
    with ui.column() as contenedor:
        try:
            campo = crear_campo_funcion()
            assert campo._props.get("data-simbolos") == "funcion"
            assert "Control+Shift+Space" in campo._props.get("aria-keyshortcuts", "")
            assert "append" not in campo.slots
            assert "hint" in campo.slots
            assert "Ctrl+Mayús+Espacio para abrir Símbolos" in (campo.slots["hint"].template or "")
        finally:
            contenedor.delete()


def test_plantilla_simbolos_mantiene_cabecera_fija_y_dialogo_nativo():
    """La plantilla usa dialog nativo con closedby, cabecera separada y cierre etiquetado."""
    ruta_plantilla = RAIZ / "src/frontend/recursos/plantillas/cabecera/simbolos.html"
    html = ruta_plantilla.read_text(encoding="utf-8")

    assert '<dialog class="simbolos-dialogo" aria-labelledby="titulo-simbolos" closedby="any">' in html
    assert 'role="dialog"' not in html
    assert "aria-modal" not in html
    assert html.index('<header class="simbolos-cabecera">') < html.index("</header>")
    assert html.index("</header>") < html.index('<div class="simbolos-cuerpo">')
    assert 'aria-label="Cerrar selector de símbolos"' in html


def test_estilos_selector_simbolos_acotan_flex_y_scroll_interno():
    """Los estilos acotan display al estado abierto y contienen el scroll en cuerpo y backdrop."""
    ruta_css = RAIZ / "src/frontend/recursos/css/componentes/selector_simbolos.css"
    texto_css = ruta_css.read_text(encoding="utf-8")

    regla_dialogo = _bloque_css(texto_css, ".simbolos-dialogo")
    regla_abierto = _bloque_css(texto_css, ".simbolos-dialogo[open]")
    regla_backdrop = _bloque_css(texto_css, ".simbolos-dialogo::backdrop")
    regla_cabecera = _bloque_css(texto_css, ".simbolos-cabecera")
    regla_cuerpo = _bloque_css(texto_css, ".simbolos-cuerpo")

    assert "display" not in regla_dialogo
    assert "display: flex" in regla_abierto
    assert "overflow: hidden" in regla_backdrop
    assert "overscroll-behavior: contain" in regla_backdrop
    assert "flex-shrink: 0" in regla_cabecera
    assert "min-height: 0" in regla_cuerpo
    assert "overflow-y: auto" in regla_cuerpo
