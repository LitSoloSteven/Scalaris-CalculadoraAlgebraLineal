"""Duraciones de entrada, gesto y pulsación del directorio de inicio."""
from pathlib import Path
import re
from tests.comun_estilos import leer_css_inicio, bloque_css


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


def test_temporizacion_directorio_y_accesibilidad():
    """El directorio conserva tiempos de entrada, pulsación, gesto y accesibilidad."""
    css = leer_css_inicio()
    js = RUTA_JS_INICIO.read_text(encoding="utf-8")
    _comprobar_duraciones_permitidas(css)
    _comprobar_duraciones_entrada_y_gesto(css, js)
    _comprobar_duraciones_pulsacion(css)
    _comprobar_accesibilidad(css)


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


def _comprobar_duraciones_entrada_y_gesto(css, js):
    seccion = bloque_css(css, ".inicio-seccion {")
    assert duracion_milisegundos(seccion, "transition") == 600
    assert "opacity: 0" in bloque_css(css, ".inicio-seccion:not(:focus-within)")
    assert "var(--stagger-step)" in seccion and "var(--stagger-max)" in seccion
    assert "--dur-state" in js
    assert ".animate(" in js


def _comprobar_duraciones_pulsacion(css):
    reposo = bloque_css(css, ".inicio-simbolo {")
    pulsacion = bloque_css(css, ".inicio-enlace:active .inicio-simbolo")
    assert duracion_milisegundos(reposo, "transition") == 320
    assert duracion_milisegundos(pulsacion, "transition-duration") == 200
    assert duracion_milisegundos(reposo, "transition") > duracion_milisegundos(pulsacion, "transition-duration")


def _comprobar_accesibilidad(css):
    teclado = bloque_css(css, 'html[data-entrada="teclado"] :is(.inicio-seccion, .inicio-simbolo)')
    movimiento_reducido = bloque_css(css, "@media (prefers-reduced-motion: reduce)")
    assert "transition: none" in teclado
    assert "transform: none" in movimiento_reducido
    assert "transition: opacity var(--dur-reduced) var(--ease-std)" in movimiento_reducido
    assert duracion_milisegundos(movimiento_reducido, "transition") == 120
