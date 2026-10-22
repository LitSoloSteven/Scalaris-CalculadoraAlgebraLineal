"""Duración de entrada y salida de los diálogos del inicio."""
from pathlib import Path
import re
from tests.comun_estilos import leer_css_inicio, bloque_css


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/theme.css")
RUTA_JS_INICIO = Path("src/frontend/recursos/js/inicio.js")


def duracion_milisegundos(bloque: str, nombre_propiedad: str) -> int:
    """Extrae la duración explícita de una propiedad del bloque CSS."""
    coincidencia = re.search(rf"\b{re.escape(nombre_propiedad)}\s*:\s*([^;]+)", bloque)
    assert coincidencia is not None, f"Falta {nombre_propiedad} en el bloque"
    duracion = re.search(r"(\d+)ms\b", coincidencia.group(1))
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
    assert duraciones
    assert max(duraciones) <= 250
    assert not re.search(r"(?<![\w-])ease-in(?![\w-])", css, re.IGNORECASE)


def _comprobar_duraciones_dialogos(css):
    salida_tarjeta = bloque_css(css, ".inicio-dialogo-tarjeta")
    entrada_tarjeta = bloque_css(css, ".inicio-dialogo[open][data-abierto] .inicio-dialogo-tarjeta")
    assert "opacity: 0" in salida_tarjeta
    assert duracion_milisegundos(salida_tarjeta, "transition") == 180
    assert duracion_milisegundos(entrada_tarjeta, "transition-duration") == 250
    assert duracion_milisegundos(entrada_tarjeta, "transition-duration") > duracion_milisegundos(salida_tarjeta, "transition")

    movil = bloque_css(css, "@media (max-width: 639px)")
    salida_movil = bloque_css(movil, ".inicio-dialogo-tarjeta")
    entrada_movil = bloque_css(movil, ".inicio-dialogo[open][data-abierto] .inicio-dialogo-tarjeta")
    assert duracion_milisegundos(salida_movil, "transition-duration") == 200
    assert duracion_milisegundos(entrada_movil, "transition-duration") == 250
    assert duracion_milisegundos(entrada_movil, "transition-duration") > duracion_milisegundos(salida_movil, "transition-duration")


def _comprobar_duraciones_tarjetas(css):
    entrada_fondo = bloque_css(css, ".inicio-dialogo[open][data-abierto]::backdrop")
    assert duracion_milisegundos(entrada_fondo, "transition-duration") == 250
    entrada_ficha = bloque_css(css, ".inicio-dialogo[data-abierto] .inicio-tarjeta")
    assert duracion_milisegundos(entrada_ficha, "transition-duration") == 120
    assert "calc(var(--i, 0) * 40ms)" in entrada_ficha


def _comprobar_cierre_y_accesibilidad(js, css):
    respaldo = re.search(
        r"temporizadorCierre = setTimeout\(function \(\) \{ finalizar_cierre\(dialogo\); \}, (\d+)\)",
        js,
    )
    assert respaldo is not None
    assert int(respaldo.group(1)) <= 250
    assert "tarjeta.addEventListener('transitionend', manejar_transicion_cierre);" in js
    assert "evento.target === tarjeta && evento.propertyName === 'opacity'" in js
    assert "cancelar_espera_cierre();" in js
    assert "if (temporizadorCierre && dialogoCerrandose === dialogo) return;" in js
    assert js.count("temporizadorCierre = setTimeout(") == 1

    teclado = bloque_css(css, 'html[data-entrada="teclado"] .inicio-fila,')
    movimiento_reducido = bloque_css(css, "@media (prefers-reduced-motion: reduce)")
    assert "transition: none !important" in teclado
    assert "transition: opacity 120ms linear" in movimiento_reducido
