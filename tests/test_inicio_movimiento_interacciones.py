"""Movimiento de filas, halo del puntero y diálogos del inicio."""
from pathlib import Path
import re

from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, razon_contraste,
    leer_css_inicio, buscar_cierre_bloque, bloque_css,
)


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/theme.css")
RUTA_JS_INICIO = Path("src/frontend/recursos/js/inicio.js")
RUTA_VISTA_INICIO = Path("src/frontend/vistas/inicio/vista_inicio.py")


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
            assert float(duracion) <= 250, declaracion
    assert not re.search(r"\bease-in\b", css, re.IGNORECASE)


def test_teclado_y_movimiento_reducido_desactivan_transformaciones():
    """Teclado y preferencia de movimiento reducido evitan animaciones físicas."""
    css = leer_css_inicio()
    inicio_teclado = css.index('html[data-entrada="teclado"] .inicio-fila,')
    apertura_teclado = css.index("{", inicio_teclado)
    teclado = css[inicio_teclado:buscar_cierre_bloque(css, apertura_teclado) + 1]
    movimiento_reducido = bloque_css(css, "@media (prefers-reduced-motion: reduce)")

    assert "transition: none !important" in teclado
    assert "transition-delay: 0ms !important" in teclado
    assert ".inicio-dialogo-tarjeta" in teclado
    assert ".inicio-tarjeta" in teclado
    assert "inicio-capa-destacada" in teclado
    assert "transition: opacity 120ms linear" in movimiento_reducido
    assert "transform: none !important" in movimiento_reducido
    assert "transition-delay: 0ms !important" in movimiento_reducido
    assert ".inicio-fila" in movimiento_reducido
    assert ".inicio-dialogo-tarjeta" in movimiento_reducido
    assert ".inicio-tarjeta" in movimiento_reducido
    assert ".inicio-capa-destacada" in movimiento_reducido


def test_filas_y_tarjetas_inicio_limitan_retardos():
    """Los índices limitados mantienen los retardos y el arranque tras la pantalla inicial."""
    vista = RUTA_VISTA_INICIO.read_text(encoding="utf-8")
    css = leer_css_inicio()
    js = RUTA_JS_INICIO.read_text(encoding="utf-8")

    assert "_CLASES_ORDEN[indice_fila]" in vista
    assert "_CLASES_ORDEN[min(indice_tarjeta, 3)]" in vista
    assert "calc(var(--i, 0) * 40ms)" in bloque_css(css, ".inicio-fila")
    assert "calc(var(--i, 0) * 40ms)" in bloque_css(css, ".inicio-dialogo[data-abierto] .inicio-tarjeta")
    assert "min(indice_tarjeta, 3)" in vista
    assert "evento.detail === 0" in js
    assert "html[data-entrada=\"teclado\"]" in css
    assert "limiteEsperaPendiente = Date.now() + 3400" in js
    assert "aplicacion-presentacion-fondo" in js
    assert "new MutationObserver" in js


def test_halo_puntero_limita_cuadros_y_solo_mueve_su_capa():
    """El halo agrupa eventos por cuadro y respeta táctil y movimiento reducido."""
    js = RUTA_JS_INICIO.read_text(encoding="utf-8")
    inicio = js.index("  function mover_destacada(fila, evento) {")
    fin = js.index("  function limpiar_destacada_al_salir_puntero(evento) {", inicio)
    manejador_halo = js[inicio:fin]

    assert "window.requestAnimationFrame" in manejador_halo
    assert "fotogramasDestacada.has(fila)" in manejador_halo
    assert "posicionesDestacada.set(fila" in manejador_halo
    assert "destacada.style.transform = 'translate3d('" in manejador_halo
    assert ".style." not in manejador_halo.replace("destacada.style.transform", "")
    assert "data-destacada-activa" in js
    assert "pointermove" in js
    assert "pointerout" in js
    assert "evento.pointerType === 'touch'" in js
    assert "prefers-reduced-motion: reduce" in js


def test_token_halo_definido_y_contraste_texto_aa():
    """La mezcla del halo mantiene contraste de texto en los tres temas."""
    from tests.comun import leer_css_completo
    css_completo = leer_css_completo()
    css = leer_css_inicio()
    tokens = analizar_tokens("src/frontend/recursos/css/tokens.css", pasadas=1, exigir_cierre=False)

    assert css_completo.count("--hub-spot:") == 4
    assert "color-mix(in srgb, var(--accent) var(--hub-spot), transparent)" in css
    for nombre_tema in ("papel", "marea", "medianoche"):
        tema = tokens[nombre_tema]
        porcentaje = float(tema["--hub-spot"].rstrip("%")) / 100
        panel = hexadecimal_a_rgb(tema["--bg-panel"], limpiar_espacios=False)
        acento = hexadecimal_a_rgb(tema["--accent"], limpiar_espacios=False)
        fondo_halo = tuple(
            porcentaje * canal_acento + (1 - porcentaje) * canal_panel
            for canal_acento, canal_panel in zip(acento, panel)
        )
        for color_frente in ("--text-main", "--text-sec"):
            proporcion = razon_contraste(hexadecimal_a_rgb(tema[color_frente], limpiar_espacios=False), fondo_halo)
            assert proporcion >= 4.5, (
                f"Contraste de {color_frente} en {nombre_tema}: {proporcion:.2f}:1 < 4.5:1"
            )


def test_cierre_dialogo_espera_transicion_y_tiene_respaldo():
    """El cierre termina por evento de opacidad o por el temporizador de respaldo."""
    js = RUTA_JS_INICIO.read_text(encoding="utf-8")
    css = leer_css_inicio()

    assert "tarjeta.style.transformOrigin" in js
    assert "if (inmediato) tarjeta.style.removeProperty('transform-origin')" in js
    assert "cancelar_espera_cierre();" in js
    assert "dialogo.removeAttribute('data-abierto')" in js
    assert "evento.propertyName === 'opacity'" in js
    assert "setTimeout(function () { finalizar_cierre(dialogo); }, 220)" in js
    assert "dialogo.close()" in js
    assert "transition: opacity 180ms var(--ease-std)" in css
    assert "transition: opacity 180ms linear, transform 200ms var(--ease-std)" in css
    assert "transition-duration: 250ms" in css
    assert "transform: translateY(100%)" in css
    assert "transition-duration: 200ms" in css
