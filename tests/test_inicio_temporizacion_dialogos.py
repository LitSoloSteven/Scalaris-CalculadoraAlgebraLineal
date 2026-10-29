"""Duración de entrada y salida de los diálogos del inicio."""
from pathlib import Path
import re
from tests.comun_estilos import leer_css_inicio, bloque_css


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/theme.css")
RUTA_JS_INICIO = Path("src/frontend/recursos/js/inicio.js")


def duracion_milisegundos(bloque: str, nombre_propiedad: str) -> int:
    """Resuelve la duración literal o el token de una propiedad del bloque CSS."""
    coincidencia = re.search(rf"\b{re.escape(nombre_propiedad)}\s*:\s*([^;]+)", bloque)
    assert coincidencia is not None, f"Falta {nombre_propiedad} en el bloque"
    declaracion = coincidencia.group(1)
    token = re.search(r"var\((--dur-[a-z-]+)\)", declaracion)
    if token:
        tokens = Path("src/frontend/recursos/css/tokens.css").read_text(encoding="utf-8")
        duracion = re.search(rf"{re.escape(token.group(1))}:\s*(\d+)ms\b", tokens)
    else:
        duracion = re.search(r"(\d+)ms\b", declaracion)
    assert duracion is not None, f"Falta duración en {nombre_propiedad}"
    return int(duracion.group(1))


def test_temporizacion_dialogos_y_accesibilidad():
    """Conserva duraciones de diálogos, tarjetas, teclado y movimiento reducido."""
    css = leer_css_inicio()
    js = RUTA_JS_INICIO.read_text(encoding="utf-8")
    _comprobar_duraciones_permitidas(css)
    _comprobar_duraciones_dialogos(css)
    _comprobar_duraciones_tarjetas(css)
    _comprobar_cierre_y_accesibilidad(js, css)


def _comprobar_duraciones_permitidas(css):
    declaraciones_transicion = re.findall(
        r"\btransition(?:-duration)?\s*:\s*([^;]+);",
        css,
        flags=re.IGNORECASE,
    )
    duraciones = [
        int(valor)
        for declaracion in declaraciones_transicion
        for valor in re.findall(r"(?<![\w.])(\d+)ms\b", declaracion)
    ]
    assert declaraciones_transicion
    assert max(duraciones, default=0) <= 900
    tokens = Path("src/frontend/recursos/css/tokens.css").read_text(encoding="utf-8")
    nombres = set(re.findall(r"var\((--dur-[a-z-]+)\)", " ".join(declaraciones_transicion)))
    assert nombres
    for nombre in nombres:
        coincidencia = re.search(rf"{re.escape(nombre)}:\s*(\d+)ms\b", tokens)
        assert coincidencia, nombre
        duracion = int(coincidencia.group(1))
        assert duracion == 120 if nombre == '--dur-reduced' else 200 <= duracion <= 900
    assert not re.search(r"(?<![\w-])ease-in(?![\w-])", css, re.IGNORECASE)


def _comprobar_duraciones_dialogos(css):
    salida_tarjeta = bloque_css(css, ".inicio-dialogo-tarjeta")
    entrada_tarjeta = bloque_css(css, ".inicio-dialogo[open][data-abierto] .inicio-dialogo-tarjeta")
    assert "opacity: 0" in salida_tarjeta
    assert duracion_milisegundos(salida_tarjeta, "transition") == 450
    assert duracion_milisegundos(entrada_tarjeta, "transition-duration") == 600
    assert duracion_milisegundos(entrada_tarjeta, "transition-duration") > duracion_milisegundos(salida_tarjeta, "transition")

    movil = bloque_css(css, "@media (max-width: 639px)")
    salida_movil = bloque_css(movil, ".inicio-dialogo-tarjeta")
    entrada_movil = bloque_css(movil, ".inicio-dialogo[open][data-abierto] .inicio-dialogo-tarjeta")
    assert duracion_milisegundos(salida_movil, "transition-duration") == 450
    assert duracion_milisegundos(entrada_movil, "transition-duration") == 600
    assert duracion_milisegundos(entrada_movil, "transition-duration") > duracion_milisegundos(salida_movil, "transition-duration")


def _comprobar_duraciones_tarjetas(css):
    entrada_fondo = bloque_css(css, ".inicio-dialogo[open][data-abierto]::backdrop")
    assert duracion_milisegundos(entrada_fondo, "transition-duration") == 600
    entrada_ficha = bloque_css(css, ".inicio-dialogo[data-abierto] .inicio-tarjeta")
    assert duracion_milisegundos(entrada_ficha, "transition-duration") == 600
    assert "var(--stagger-step)" in entrada_ficha and "var(--stagger-max)" in entrada_ficha


def _comprobar_cierre_y_accesibilidad(js, css):
    respaldo = re.search(
        r"temporizadorCierre = setTimeout\(function \(\) \{ finalizar_cierre\(dialogo\); \}, window.scalaris.movimiento.duracion\('--dur-view-exit'\) \+ 50\)",
        js,
    )
    assert respaldo is not None
    assert "tarjeta.addEventListener('transitionend', manejar_transicion_cierre);" in js
    assert "evento.target === tarjeta && evento.propertyName === 'opacity'" in js
    assert "cancelar_espera_cierre();" in js
    assert "if (temporizadorCierre && dialogoCerrandose === dialogo) return;" in js
    assert js.count("temporizadorCierre = setTimeout(") == 1

    teclado = bloque_css(css, 'html[data-entrada="teclado"] .inicio-fila,')
    movimiento_reducido = bloque_css(css, "@media (prefers-reduced-motion: reduce)")
    assert "transition: none !important" in teclado
    assert "transition: opacity var(--dur-reduced) var(--ease-std)" in movimiento_reducido
