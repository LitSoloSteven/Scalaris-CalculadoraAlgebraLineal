"""Contratos de disposición común, logotipo único en navegación y selectores unificados."""
import ast
import asyncio
from pathlib import Path
import re

from nicegui import Client, core, ui

from src.frontend.componentes.aplicacion.base.iconos import icono_svg
from src.frontend.componentes.aplicacion.controles.barra_navegacion import crear_barra_navegacion
from src.frontend.componentes.aplicacion.controles.selector_opciones import SelectorOpciones
from src.frontend.nucleo.textos.textos_espacio_vectorial import MODO_PERSONALIZADO
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.comun_estilos import bloque_css


def test_disposicion_comun_asigna_pistas_sin_recortar_grid():
    """Las pistas del grid usan ancho completo, separación acotada y cobertura en 320 px."""
    css = Path("src/frontend/recursos/css/base/disposicion.css").read_text(encoding="utf-8")
    bloque_dividida = bloque_css(css, ".disposicion-dividida {")
    bloque_panel_dividido = bloque_css(css, ".disposicion-dividida > .disposicion-panel {")
    bloque_captura = bloque_css(css, ".disposicion-captura-fila {")
    bloque_hijos = bloque_css(css, ".disposicion-captura-fila > * {")
    assert "width: 50%" not in css
    assert "flex: 1 1 0%;" in bloque_panel_dividido
    assert "width: auto;" in bloque_panel_dividido
    assert "width: 100%;" in bloque_hijos and "min-width: 0;" in bloque_hijos
    for bloque in (bloque_dividida, bloque_captura):
        assert re.search(r"gap:\s*var\(--space-[456]\);", bloque)
    assert "@media (max-width: 280px)" not in css
    assert "@media (max-width: 360px)" in css


def _construir_barra_prueba(monkeypatch, valor_nav: str):
    """Construye la barra de navegación aislada para el modo indicado."""
    monkeypatch.setattr(core, "script_mode", False)
    monkeypatch.setenv("SCALARIS_NAV", valor_nav)
    cliente = Client(ui.page(f"/prueba_logo_nav_{valor_nav}"))
    with cliente:
        crear_barra_navegacion(ruta_activa="/algebra-lineal/sistemas")
    return cliente


def test_barra_contextual_usa_logotipo_unico_sin_icono_duplicado(monkeypatch):
    """La barra contextual reemplaza la casa por el logotipo sin duplicar el enlace a inicio."""
    cliente_contextual = _construir_barra_prueba(monkeypatch, "1")
    try:
        cabecera = next(el for el in cliente_contextual.elements.values() if "navegacion-cabecera" in el.classes)
        enlaces_inicio = [
            el for el in cabecera.descendants()
            if el._props.get("href") == "/" or "marca-enlace-esquina" in el.classes
        ]
        assert len(enlaces_inicio) == 1
        enlace = enlaces_inicio[0]
        assert "navegacion-inicio" in enlace.classes
        assert enlace._props.get("aria-label") == "Inicio"
        contenido_html = "".join(
            getattr(hijo, "content", "") for hijo in enlace.descendants() if isinstance(hijo, ui.html)
        )
        assert "/assets/LogoOscuro.png" in contenido_html
        assert "/assets/LogoClaro.png" in contenido_html
        assert icono_svg("inicio") not in contenido_html
    finally:
        cliente_contextual.delete()


def test_barra_plana_conserva_logotipo_de_esquina(monkeypatch):
    """El modo clásico conserva el logotipo único de esquina sin botón duplicado."""
    cliente_plano = _construir_barra_prueba(monkeypatch, "0")
    try:
        cabecera_plana = next(el for el in cliente_plano.elements.values() if "navegacion-cabecera" in el.classes)
        esquinas = [el for el in cabecera_plana.descendants() if "marca-enlace-esquina" in el.classes]
        inicios = [el for el in cabecera_plana.descendants() if "navegacion-inicio" in el.classes]
        assert len(esquinas) == 1
        assert inicios == []
    finally:
        cliente_plano.delete()


def test_operaciones_personalizadas_usa_selector_comun_y_desplegable_estilizado(monkeypatch):
    """La definición del conjunto usa SelectorOpciones y el selector de ejemplos usa el estilo común."""
    monkeypatch.setitem(VISTAS_RUTAS, "espacios_subespacios", (
        "algebra.operaciones_vectores.vista_espacios_subespacios", "VistaEspaciosSubespacios",
    ))

    async def _comprobar(vista, _cliente):
        """Comprueba el selector de conjunto y el desplegable de ejemplos."""
        captura = vista.captura
        assert isinstance(captura._selector_conjunto, SelectorOpciones)
        assert captura._selector_conjunto._props.get("role") == "radiogroup"
        captura._selector_conjunto.set_value("restricciones")
        assert captura._modo_conjunto == "restricciones"
        assert captura._selectores_conjunto["restricciones"].visible
        assert not captura._selectores_conjunto["generadores"].visible
        captura._selector_conjunto.set_value("generadores")
        assert captura._modo_conjunto == "generadores"
        assert captura._selectores_conjunto["generadores"].visible
        assert captura._selector_ejemplo is None

    asyncio.run(construir_pagina(monkeypatch, "espacios_subespacios", _comprobar, {"modo": MODO_PERSONALIZADO}))


def test_iterativos_estiliza_selector_decimales(monkeypatch):
    """El selector de decimales en métodos iterativos usa el patrón común sin outlined."""
    monkeypatch.setitem(VISTAS_RUTAS, "metodos_iterativos", (
        "algebra.sistemas_lineales.vista_metodos_iterativos", "VistaMetodosIterativos",
    ))

    async def _comprobar(vista, _cliente):
        """Verifica las clases y propiedades del desplegable de decimales."""
        selector = vista.selector_decimales
        assert "selector-controles" in selector.classes
        assert selector._props.get("popup-content-class") == "selector-menu"
        assert "outlined" not in selector._props

    asyncio.run(construir_pagina(monkeypatch, "metodos_iterativos", _comprobar))


def _es_llamada_ui_select(nodo: ast.AST) -> bool:
    """Indica si el nodo AST corresponde a una llamada a ui.select."""
    return (
        isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "select"
        and isinstance(nodo.func.value, ast.Name)
        and nodo.func.value.id == "ui"
    )


def _selects_sin_estilo(ruta: Path) -> list[str]:
    """Devuelve las ubicaciones de ui.select sin estilo común dentro de un archivo."""
    texto = ruta.read_text(encoding="utf-8")
    lineas = texto.splitlines()
    faltantes = []
    for nodo in ast.walk(ast.parse(texto, filename=str(ruta))):
        if not _es_llamada_ui_select(nodo):
            continue
        ventana = "\n".join(lineas[max(0, nodo.lineno - 4):min(len(lineas), nodo.end_lineno + 4)])
        if "estilizar_desplegable" not in ventana and not ("selector-controles" in ventana and "selector-menu" in ventana):
            faltantes.append(f"{ruta.as_posix()}:{nodo.lineno}")
    return faltantes


def test_todos_los_ui_select_de_interfaz_usan_estilo_comun():
    """Ningún ui.select en src/frontend queda fuera del helper o clases comunes de Scalaris."""
    faltantes = [ubicacion for ruta in sorted(Path("src/frontend").rglob("*.py")) for ubicacion in _selects_sin_estilo(ruta)]
    assert faltantes == [], f"ui.select sin estilo común: {faltantes}"
