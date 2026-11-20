"""Contratos del selector de símbolos sin botón visible y diálogo con cabecera fija."""
import re
from html.parser import HTMLParser

from nicegui import ui

from src.frontend.componentes.campo_funcion_real import crear_campo_funcion
from src.frontend.componentes.simbolos import habilitar_simbolos
from tests.comun import RAIZ


class _AnalizadorPlantillaSimbolos(HTMLParser):
    """Recorre etiquetas, atributos y jerarquía de la plantilla del selector."""

    def __init__(self) -> None:
        super().__init__()
        self.pila: list[str] = []
        self.dialogo_attrs: dict[str, str | None] | None = None
        self.cabecera_en_cuerpo = False
        self.boton_cerrar: dict[str, str | None] | None = None
        self.cuerpo_presente = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        diccionario = dict(attrs)
        clases = (diccionario.get("class") or "").split()
        if tag == "dialog" and "simbolos-dialogo" in clases:
            self.dialogo_attrs = diccionario
        if tag == "div" and "simbolos-cuerpo" in clases:
            self.cuerpo_presente = True
        if tag == "header" and "simbolos-cabecera" in clases and "simbolos-cuerpo" in self.pila:
            self.cabecera_en_cuerpo = True
        if tag == "button" and diccionario.get("type") == "submit" and "form" in self.pila:
            self.boton_cerrar = diccionario
        self.pila.append("simbolos-cuerpo" if "simbolos-cuerpo" in clases else tag)

    def handle_endtag(self, tag: str) -> None:
        if self.pila:
            self.pila.pop()


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
    ruta_plantilla = RAIZ / "src/frontend/recursos/plantillas/simbolos.html"
    analizador = _AnalizadorPlantillaSimbolos()
    analizador.feed(ruta_plantilla.read_text(encoding="utf-8"))

    assert analizador.dialogo_attrs is not None
    assert analizador.dialogo_attrs.get("aria-labelledby") == "titulo-simbolos"
    assert analizador.dialogo_attrs.get("closedby") == "any"
    assert "role" not in analizador.dialogo_attrs
    assert "aria-modal" not in analizador.dialogo_attrs
    assert analizador.cuerpo_presente is True
    assert analizador.cabecera_en_cuerpo is False
    assert analizador.boton_cerrar is not None
    assert bool((analizador.boton_cerrar.get("aria-label") or "").strip())


def test_estilos_selector_simbolos_acotan_flex_y_scroll_interno():
    """Los estilos acotan display al estado abierto y contienen el scroll en cuerpo y backdrop."""
    ruta_css = RAIZ / "src/frontend/recursos/css/selector_simbolos.css"
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
