"""Duración de entrada y salida de los diálogos del Hub."""
from pathlib import Path
import re
from tests.comun_estilos import leer_css_hub, bloque_css


THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
HUB_JS_PATH = Path("src/frontend/assets/js/hub.js")


def duracion_milisegundos(block: str, property_name: str) -> int:
    """Extrae la duración explícita de una propiedad del bloque CSS."""
    match = re.search(rf"\b{re.escape(property_name)}\s*:\s*([^;]+)", block)
    assert match is not None, f"Falta {property_name} en el bloque"
    duration = re.search(r"(\d+)ms\b", match.group(1))
    assert duration is not None, f"Falta duración en {property_name}"
    return int(duration.group(1))


def test_temporizacion_dialogos_y_accesibilidad():
    """Conserva duraciones de diálogos, tarjetas, teclado y movimiento reducido."""
    css = leer_css_hub()
    js = HUB_JS_PATH.read_text(encoding="utf-8")
    _comprobar_duraciones_permitidas(css)
    _comprobar_duraciones_dialogos(css)
    _comprobar_duraciones_tarjetas(css)
    _comprobar_cierre_y_accesibilidad(js, css)


def _comprobar_duraciones_permitidas(css):
    transition_declarations = re.findall(
        r"\btransition(?:-duration)?\s*:\s*([^;]+);",
        css,
        flags=re.IGNORECASE,
    )
    durations = [
        int(value)
        for declaration in transition_declarations
        for value in re.findall(r"(?<![\w.])(\d+)ms\b", declaration)
    ]
    assert durations
    assert max(durations) <= 250
    assert not re.search(r"(?<![\w-])ease-in(?![\w-])", css, re.IGNORECASE)


def _comprobar_duraciones_dialogos(css):
    card_exit = bloque_css(css, ".hub-pop-card")
    card_entry = bloque_css(css, ".hub-pop[open][data-open] .hub-pop-card")
    assert "opacity: 0" in card_exit
    assert duracion_milisegundos(card_exit, "transition") == 180
    assert duracion_milisegundos(card_entry, "transition-duration") == 250
    assert duracion_milisegundos(card_entry, "transition-duration") > duracion_milisegundos(card_exit, "transition")

    mobile = bloque_css(css, "@media (max-width: 639px)")
    mobile_exit = bloque_css(mobile, ".hub-pop-card")
    mobile_entry = bloque_css(mobile, ".hub-pop[open][data-open] .hub-pop-card")
    assert duracion_milisegundos(mobile_exit, "transition-duration") == 200
    assert duracion_milisegundos(mobile_entry, "transition-duration") == 250
    assert duracion_milisegundos(mobile_entry, "transition-duration") > duracion_milisegundos(mobile_exit, "transition-duration")


def _comprobar_duraciones_tarjetas(css):
    backdrop_entry = bloque_css(css, ".hub-pop[open][data-open]::backdrop")
    assert duracion_milisegundos(backdrop_entry, "transition-duration") == 250
    tile_entry = bloque_css(css, ".hub-pop[data-open] .hub-tile")
    assert duracion_milisegundos(tile_entry, "transition-duration") == 220
    assert "calc(var(--i, 0) * 50ms)" in tile_entry


def _comprobar_cierre_y_accesibilidad(js, css):
    fallback = re.search(
        r"closeTimer = setTimeout\(function \(\) \{ finishClose\(dialog\); \}, (\d+)\)",
        js,
    )
    assert fallback is not None
    assert int(fallback.group(1)) <= 250
    assert "card.addEventListener('transitionend', closeTransitionHandler);" in js
    assert "event.target === card && event.propertyName === 'opacity'" in js
    assert "cancelCloseWait();" in js
    assert "if (closeTimer && closingDialog === dialog) return;" in js
    assert js.count("closeTimer = setTimeout(") == 1

    keyboard = bloque_css(css, 'html[data-input="keyboard"] .hub-row,')
    reduced = bloque_css(css, "@media (prefers-reduced-motion: reduce)")
    assert "transition: none !important" in keyboard
    assert "transition: opacity 120ms linear" in reduced
