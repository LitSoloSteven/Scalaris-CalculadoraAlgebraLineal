"""Movimiento, puntero y contraste del directorio de inicio."""
from pathlib import Path
import re

from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, razon_contraste,
    leer_css_inicio, bloque_css,
)


RUTA_JS_INICIO = Path("src/frontend/recursos/js/inicio/inicio.js")
RUTA_JS_ENTRADA = Path("src/frontend/recursos/js/inicio/inicio_entrada.js")


def test_transiciones_inicio_solo_transformacion_y_opacidad():
    """Las transiciones conservan propiedades y duración permitidas."""
    css = leer_css_inicio()
    declaraciones = re.findall(
        r"\btransition(?:-property)?(?![-\w])\s*:\s*([^;]+);",
        css,
        re.IGNORECASE,
    )
    assert declaraciones
    prohibidos = re.compile(
        r"\b(?:width|height|margin(?:-[a-z-]+)?|padding(?:-[a-z-]+)?|"
        r"left|top|box-shadow)\b",
        re.IGNORECASE,
    )
    for declaracion in declaraciones:
        assert not prohibidos.search(declaracion), declaracion
        for duracion in re.findall(r"([\d.]+)ms\b", declaracion):
            assert float(duracion) <= 900, declaracion
    assert not re.search(r"\bease-in\b", css, re.IGNORECASE)


def test_teclado_y_movimiento_reducido_desactivan_transformaciones():
    """El teclado revela las secciones al instante y el movimiento reducido usa opacidad."""
    css = leer_css_inicio()
    teclado = bloque_css(css, 'html[data-entrada="teclado"] :is(.inicio-seccion, .inicio-simbolo)')
    movimiento_reducido = bloque_css(css, "@media (prefers-reduced-motion: reduce)")

    assert "opacity: 1" in teclado
    assert "transform: none" in teclado
    assert "transition: none" in teclado
    assert ".inicio-seccion:focus-within" in css
    assert "transition: opacity var(--dur-reduced) var(--ease-std)" in movimiento_reducido
    assert "transform: none" in movimiento_reducido
    assert ".inicio-seccion" in movimiento_reducido
    assert ".inicio-simbolo" in movimiento_reducido
    assert 'html:not([data-entrada="teclado"]) .inicio-enlace:active .inicio-simbolo' in css


def test_secciones_inicio_limitan_retardos():
    """El escalonado de secciones espera el montaje y tiene un tope compartido."""
    css = leer_css_inicio()
    seccion = bloque_css(css, ".inicio-seccion {")
    assert "min(calc(var(--inicio-indice, 0) * var(--stagger-step)), var(--stagger-max))" in seccion
    assert "var(--dur-view)" in seccion
    assert "html[data-inicio-pendiente]" in css

    entrada = RUTA_JS_ENTRADA.read_text(encoding="utf-8")
    assert ".inicio-directorio[data-directorio-listo]" in entrada
    assert "{ directorioListo, finalizar }" in entrada
    assert "new MutationObserver" in entrada
    assert "requestAnimationFrame(confirmarMontaje)" in entrada


def test_gesto_puntero_solo_mueve_los_trazos_del_simbolo():
    """El gesto usa la capa vectorial, puntero preciso y la preferencia de movimiento."""
    js = RUTA_JS_INICIO.read_text(encoding="utf-8")

    assert "data-gesto-inicio" in js
    assert ".inicio-simbolo" in js
    assert ".animate(" in js
    assert re.search(r"\bcancel(?:\?\.)?\(", js)
    assert "--dur-state" in js
    assert "pointerenter" in js or "pointerover" in js
    assert "pointercancel" in js and ".finished" in js
    assert "pointerdown" in js and "keydown" in js
    assert "pointerType" in js and re.search(r"['\"]touch['\"]", js)
    assert "(hover: hover) and (pointer: fine)" in js
    assert "prefers-reduced-motion: reduce" in js
    assert "getBoundingClientRect(" not in js
    assert "pointermove" not in js


def test_texto_y_foco_del_directorio_conservan_contraste():
    """El texto, el acento y el anillo de foco mantienen contraste en los tres temas."""
    css = leer_css_inicio()
    tokens = analizar_tokens("src/frontend/recursos/css/base/tokens.css", pasadas=1, exigir_cierre=False)
    enlace = bloque_css(css, ".inicio-enlace {")
    hover = bloque_css(css, ".inicio-enlace:hover")
    assert "color: var(--text-main)" in enlace
    assert "background: var(--bg-panel)" in hover
    assert "outline: 2px solid var(--focus-ring)" in css
    for nombre_tema, tema in tokens.items():
        for color_fondo in ("--bg-page", "--bg-panel"):
            fondo = hexadecimal_a_rgb(tema[color_fondo])
            for color_frente, minimo in (("--text-main", 4.5), ("--text-sec", 4.5),
                                        ("--accent", 3), ("--focus-ring", 3)):
                proporcion = razon_contraste(hexadecimal_a_rgb(tema[color_frente]), fondo)
                assert proporcion >= minimo, (
                    f"Contraste de {color_frente} frente a {color_fondo} en {nombre_tema}: "
                    f"{proporcion:.2f}:1 < {minimo}:1"
                )


def test_entrada_directorio_limpia_esperas_y_tiene_respaldo():
    """El montaje termina aunque falte contenido y libera sus recursos con pagehide."""
    entrada = RUTA_JS_ENTRADA.read_text(encoding="utf-8")

    assert re.search(r"setTimeout\(finalizar,\s*(?:5_?000)\)", entrada)
    assert "clearTimeout(" in entrada
    assert "cancelAnimationFrame(" in entrada
    assert ".disconnect()" in entrada
    assert "addEventListener('pagehide', finalizar)" in entrada
    assert "removeEventListener('pagehide', finalizar)" in entrada
    assert "removeAttribute('data-inicio-pendiente')" in entrada
