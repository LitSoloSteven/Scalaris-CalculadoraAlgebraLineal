"""Movimiento de filas, halo del puntero y diálogos del Hub."""
from pathlib import Path
import re

from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, razon_contraste,
    leer_css_hub, buscar_cierre_bloque, bloque_css,
)


THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")
VIEW_HUB_PATH = Path("src/frontend/vistas/hub/view_hub.py")


def test_transiciones_hub_solo_transformacion_y_opacidad():
    """Las transiciones conservan propiedades y duración permitidas."""
    css = leer_css_hub()
    declarations = re.findall(
        r"\btransition(?:-property)?(?![-\w])\s*:\s*([^;]+);",
        css,
        re.IGNORECASE,
    )
    assert declarations
    forbidden = re.compile(
        r"\b(?:width|height|margin(?:-[a-z-]+)?|padding(?:-[a-z-]+)?|"
        r"left|top|box-shadow)\b",
        re.IGNORECASE,
    )
    for declaration in declarations:
        assert not forbidden.search(declaration), declaration
        for duration in re.findall(r"([\d.]+)ms\b", declaration):
            assert float(duration) <= 250, declaration
    assert not re.search(r"\bease-in\b", css, re.IGNORECASE)


def test_teclado_y_movimiento_reducido_desactivan_transformaciones():
    """Teclado y preferencia de movimiento reducido evitan animaciones físicas."""
    css = leer_css_hub()
    keyboard_start = css.index('html[data-input="keyboard"] .hub-row,')
    keyboard_open = css.index("{", keyboard_start)
    keyboard = css[keyboard_start:buscar_cierre_bloque(css, keyboard_open) + 1]
    reduced = bloque_css(css, "@media (prefers-reduced-motion: reduce)")

    assert "transition: none !important" in keyboard
    assert "transition-delay: 0ms !important" in keyboard
    assert ".hub-pop-card" in keyboard
    assert ".hub-tile" in keyboard
    assert "hub-spot-layer" in keyboard
    assert "transition: opacity 120ms linear" in reduced
    assert "transform: none !important" in reduced
    assert "transition-delay: 0ms !important" in reduced
    assert ".hub-row" in reduced
    assert ".hub-pop-card" in reduced
    assert ".hub-tile" in reduced
    assert ".hub-spot-layer" in reduced


def test_filas_y_tarjetas_hub_limitan_retardos():
    """Los índices limitados mantienen los retardos y el arranque tras el splash."""
    view = VIEW_HUB_PATH.read_text(encoding="utf-8")
    css = leer_css_hub()
    js = HUB_JS_PATH.read_text(encoding="utf-8")

    assert "style=\"--i:{row_index}\"" in view
    assert "style=\"--i:{min(tile_index, 3)}\"" in view
    assert "calc(var(--i, 0) * 45ms)" in css
    assert "calc(var(--i, 0) * 50ms)" in css
    assert "min(tile_index, 3)" in view
    assert "event.detail === 0" in js
    assert "html[data-input=\"keyboard\"]" in css
    assert "pendingDeadline = Date.now() + 3400" in js
    assert "agy-splash-overlay" in js
    assert "new MutationObserver" in js


def test_halo_puntero_limita_cuadros_y_solo_mueve_su_capa():
    """El halo agrupa eventos por cuadro y respeta táctil y movimiento reducido."""
    js = HUB_JS_PATH.read_text(encoding="utf-8")
    start = js.index("  function moveSpot(row, event) {")
    end = js.index("  function clearSpotForPointerOut(event) {", start)
    halo_handler = js[start:end]

    assert "window.requestAnimationFrame" in halo_handler
    assert "spotFrames.has(row)" in halo_handler
    assert "spotPositions.set(row" in halo_handler
    assert "spot.style.transform = 'translate3d('" in halo_handler
    assert ".style." not in halo_handler.replace("spot.style.transform", "")
    assert "data-spot-active" in js
    assert "pointermove" in js
    assert "pointerout" in js
    assert "event.pointerType === 'touch'" in js
    assert "prefers-reduced-motion: reduce" in js


def test_token_halo_definido_y_contraste_texto_aa():
    """La mezcla del halo mantiene contraste de texto en los tres temas."""
    from tests.comun import leer_css_completo
    full_css = leer_css_completo()
    css = leer_css_hub()
    tokens = analizar_tokens("src/frontend/assets/css/tokens.css", pasadas=1, exigir_cierre=False)

    assert full_css.count("--hub-spot:") == 4
    assert "color-mix(in srgb, var(--accent) var(--hub-spot), transparent)" in css
    for theme_name in ("papel", "marea", "medianoche"):
        theme = tokens[theme_name]
        percent = float(theme["--hub-spot"].rstrip("%")) / 100
        panel = hexadecimal_a_rgb(theme["--bg-panel"], limpiar_espacios=False)
        accent = hexadecimal_a_rgb(theme["--accent"], limpiar_espacios=False)
        halo_background = tuple(
            percent * accent_channel + (1 - percent) * panel_channel
            for accent_channel, panel_channel in zip(accent, panel)
        )
        for foreground in ("--text-main", "--text-sec"):
            ratio = razon_contraste(hexadecimal_a_rgb(theme[foreground], limpiar_espacios=False), halo_background)
            assert ratio >= 4.5, (
                f"Contraste de {foreground} en {theme_name}: {ratio:.2f}:1 < 4.5:1"
            )


def test_cierre_dialogo_espera_transicion_y_tiene_respaldo():
    """El cierre termina por evento de opacidad o por el temporizador de respaldo."""
    js = HUB_JS_PATH.read_text(encoding="utf-8")
    css = leer_css_hub()

    assert "card.style.transformOrigin" in js
    assert "if (instant) card.style.removeProperty('transform-origin')" in js
    assert "cancelCloseWait();" in js
    assert "dialog.removeAttribute('data-open')" in js
    assert "event.propertyName === 'opacity'" in js
    assert "setTimeout(function () { finishClose(dialog); }, 220)" in js
    assert "dialog.close()" in js
    assert "transition: opacity 180ms var(--ease-std)" in css
    assert "transition: opacity 180ms linear, transform 200ms var(--ease-std)" in css
    assert "transition-duration: 250ms" in css
    assert "transform: translateY(100%)" in css
    assert "transition-duration: 200ms" in css
