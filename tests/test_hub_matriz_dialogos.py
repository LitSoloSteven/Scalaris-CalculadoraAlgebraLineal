"""Contratos estáticos de la matriz, los diálogos y el contraste del Hub."""
from pathlib import Path
import re

from src.frontend.vistas.hub._model import hub_pillars, initial_selection
from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, razon_contraste,
    leer_css_hub, buscar_cierre_bloque,
)


THEME_CSS_PATH = Path("src/frontend/assets/css/tokens.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")
VIEW_HUB_PATH = Path("src/frontend/vistas/hub/view_hub.py")


def quitar_comentarios(css: str) -> str:
    """Retira comentarios CSS para inspeccionar solo declaraciones activas."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def test_contrato_dom_matriz_y_dialogos_nativos():
    """Las filas controlan diálogos nativos con nombres y relaciones accesibles."""
    source = VIEW_HUB_PATH.read_text(encoding="utf-8")
    pillars = hub_pillars()

    assert len(pillars) == 3
    assert source.count("for pillar in pillars:") == 2
    assert 'role="group" aria-label="Áreas de Scalaris"' in source
    assert 'type="button" id="hub-row-{pillar.id}"' in source
    assert 'aria-haspopup="dialog" aria-expanded="false"' in source
    assert 'aria-controls="hub-pop-{pillar.id}"' in source
    assert "with ui.element('dialog').classes('hub-pop').props(dialog_props):" in source
    assert 'aria-labelledby="hub-pop-title-{pillar.id}"' in source
    assert "title.props(f'id=\"hub-pop-title-{pillar.id}\"')" in source
    assert "ui.element('dialog')" in source

    row_source = source.split("with ui.element('button').classes('hub-row')", 1)[1]
    row_source = row_source.split("self.rows[pillar.id]", 1)[0]
    assert "'h2'" not in row_source
    assert "hub-row-title" in row_source


def test_contrato_cliente_matriz_y_dialogos():
    """El cliente conserva apertura, cierre, foco y delegación de eventos."""
    source = HUB_JS_PATH.read_text(encoding="utf-8")

    recientes_source = Path("src/frontend/assets/js/hub_recientes.js").read_text(encoding="utf-8")
    assert "window.scalaris.recientes =" in recientes_source
    assert "leer: leerRecientes" in recientes_source
    assert "registrar: registrarVisita" in recientes_source
    assert "window.scalarisHubSelect" not in source
    assert "function open(" in source
    assert "function close(" in source
    assert "dialog.showModal()" in source
    assert "setAttribute('data-open'" in source
    assert "removeAttribute('data-open'" in source
    assert "event.detail === 0" in source
    assert "addEventListener('cancel'" in source
    assert "target === dialog" in source
    assert "window.__scalarisHubDelegated" in source
    assert "addEventListener('popstate'" not in source

    assert not re.search(r"addEventListener\s*\(\s*['\"]scroll['\"]", source)
    assert ".onscroll" not in source
    for removed in (
        "hub-carousel",
        "hub-viewport",
        "hub-track",
        "hub-card",
        "hub-panel",
        "hub-nav-btn",
        "ResizeObserver",
        "onPointerDown",
        "onWheel",
        "scalarisHubSelect",
    ):
        assert removed not in source

    focus_calls = re.findall(r"\.focus\(([^)]*)\)", source)
    assert focus_calls
    assert all("preventScroll" in args and "true" in args for args in focus_calls)


def test_seleccion_predeterminada_marca_fila_y_tarjeta():
    """La selección sin historial destaca sistemas en el área de álgebra."""
    source = VIEW_HUB_PATH.read_text(encoding="utf-8")
    selection = initial_selection(None)

    assert selection.pillar_id == "algebra"
    assert selection.tile_key == "sistemas"
    assert selection.has_history is False
    assert "tile.classes(add='is-featured')" in source
    assert "row.classes(add='is-featured')" in source
    assert "'Sigue aquí' if sel.has_history else 'Empieza aquí'" in source
    assert "scalarisHubSelect" not in source
    assert "catch (_) { return { ok: false, ids: [] }; }" in Path("src/frontend/assets/js/hub_recientes.js").read_text(encoding="utf-8")


def test_renderizado_herramientas_vacias_y_cantidades_variables():
    """El área vacía explica su estado y las listas admiten desplazamiento."""
    source = VIEW_HUB_PATH.read_text(encoding="utf-8")
    css = leer_css_hub()

    assert "if len(pillar.tiles) == 0:" in source
    assert "for tile_model in pillar.tiles:" in source
    assert "Esta área aún no tiene herramientas." in source
    assert ".hub-tool-list" in css
    assert "overflow-y: auto" in css
    assert "overscroll-behavior: contain" in css
    assert "overflow-wrap: anywhere" in css
    assert "-webkit-line-clamp: 2" in css

def test_css_hub_usa_tokens_y_efectos_permitidos():
    """Las reglas usan tokens definidos y evitan efectos y capas no autorizados."""
    from tests.comun import leer_css_completo
    full_css = leer_css_completo()
    css = quitar_comentarios(leer_css_hub())

    assert "100vh" not in css
    assert "backdrop-filter" not in css
    assert "blur(" not in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", css)
    removed_selectors = re.compile(
        r"\.hub-(?:carousel|viewport|track|card(?=[\s.:#\[,>]|$)|nav-btn|"
        r"panels|panel(?=[\s.:#\[,>]|$)|aug)(?![a-zA-Z0-9_-])"
    )
    assert not removed_selectors.search(css)

    defined_tokens = set(re.findall(r"(--[a-zA-Z0-9_-]+)\s*:", quitar_comentarios(full_css)))
    used_tokens = set(re.findall(r"var\(\s*(--[a-zA-Z0-9_-]+)", css))
    assert used_tokens <= defined_tokens

    elevated_z_indices = [
        int(value)
        for value in re.findall(r"z-index\s*:\s*(\d+)", css, re.IGNORECASE)
        if int(value) > 10
    ]
    assert elevated_z_indices == []


def test_hover_hub_requiere_puntero_preciso():
    """Todas las reglas hover están dentro de la consulta de puntero preciso."""
    css = quitar_comentarios(leer_css_hub())
    media_pattern = re.compile(
        r"@media\s*\(hover:\s*hover\)\s*and\s*\(pointer:\s*fine\)\s*\{",
        re.IGNORECASE,
    )
    media_ranges = []
    for match in media_pattern.finditer(css):
        open_index = css.find("{", match.start())
        media_ranges.append((match.start(), buscar_cierre_bloque(css, open_index)))

    for hover in re.finditer(r":hover\b", css):
        assert any(start < hover.start() < end for start, end in media_ranges), (
            f":hover fuera de la media query de puntero preciso: {css[hover.start()-40:hover.start()+20]}"
        )


def test_fondo_activo_definido_en_cuatro_bloques_tematicos():
    """La raíz y los tres temas conservan el token de fondo activo."""
    full_css = THEME_CSS_PATH.read_text(encoding="utf-8")
    all_blocks = re.findall(r"(:root[^\{]*)\{([^}]+)\}", full_css, re.DOTALL)
    blocks = [b for b in all_blocks if "--hub-card-active-bg" in b[1]]

    assert len(blocks) == 4
    assert full_css.count("--hub-card-active-bg:") == 4
    token = re.compile(
        r"--hub-card-active-bg\s*:\s*color-mix\(\s*in\s+srgb\s*,\s*"
        r"var\(--accent\)\s+(\d+)%\s*,\s*var\(--bg-elevated\)\s*\)"
    )
    for selector, body in blocks:
        assert token.search(body), f"Falta el token de fondo activo en {selector.strip()}"


def test_fondo_activo_conserva_contraste_en_todos_los_temas():
    """La mezcla del fondo activo mantiene contraste AA para sus textos."""
    full_css = THEME_CSS_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"--hub-card-active-bg\s*:\s*color-mix\(\s*in\s+srgb\s*,\s*"
        r"var\(--accent\)\s+(\d+)%\s*,\s*var\(--bg-elevated\)",
        full_css,
    )
    assert match is not None
    accent_percent = int(match.group(1)) / 100
    themes = analizar_tokens(THEME_CSS_PATH, pasadas=1, exigir_cierre=False)

    for theme_name in ("papel", "marea", "medianoche"):
        theme = themes[theme_name]
        accent = hexadecimal_a_rgb(theme["--accent"], limpiar_espacios=False)
        elevated = hexadecimal_a_rgb(theme["--bg-elevated"], limpiar_espacios=False)
        active_background = tuple(
            accent_percent * accent_channel + (1 - accent_percent) * elevated_channel
            for accent_channel, elevated_channel in zip(accent, elevated)
        )
        for foreground in ("--text-main", "--text-sec", "--accent"):
            ratio = razon_contraste(hexadecimal_a_rgb(theme[foreground], limpiar_espacios=False), active_background)
            assert ratio >= 4.5, (
                f"Contraste de {foreground} en {theme_name}: {ratio:.2f}:1 < 4.5:1"
            )


def test_disposicion_dialogo_y_bloqueo_desplazamiento():
    """El diálogo contiene su lista y bloquea el desplazamiento de la página."""
    css = leer_css_hub()

    assert "width: min(92vw, 42rem)" in css
    assert "max-height: min(82dvh, 44rem)" in css
    assert ".hub-pop::backdrop" in css
    assert "background: var(--scrim)" in css
    assert "html[data-hub-dialog-open]" in css
    assert "@media (max-width: 639px)" in css
    assert "max-height: 85dvh" in css
    assert "@media (max-width: 479px)" in css
    assert "grid-template-areas:\n            \"icon name\"\n            \"icon meta\"" in css
