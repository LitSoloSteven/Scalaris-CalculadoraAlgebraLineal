"""Orden de tema, estilos, presentación y coordinación de entrada del inicio."""
from pathlib import Path

from src.frontend import tema


def test_presentacion_carga_despues_de_tema_y_estilos():
    """El primer fotograma usa la paleta restaurada y las reglas ya disponibles."""
    cabecera = tema._CABECERA_HTML
    assert cabecera.index("inicializacion_tema.js") < cabecera.index("tokens.css")
    assert cabecera.index("presentacion.css") < cabecera.index("presentacion.js")
    assert cabecera.index('id="presentacion-plantilla"') < cabecera.index("presentacion.js")
    assert cabecera.index("presentacion.js") < cabecera.index("inicio_entrada.js") < cabecera.index('src="/assets/js/inicio.js"')


def test_presentacion_decorativa_no_intercepta_la_aplicacion():
    """La capa no recibe foco ni puntero y su orden se deriva de los tokens."""
    recursos = Path("src/frontend/recursos")
    css = (recursos / "css/presentacion.css").read_text(encoding="utf-8")
    plantilla = (recursos / "plantillas/presentacion.html").read_text(encoding="utf-8")
    assert "pointer-events: none;" in css
    assert "z-index: calc(var(--z-modal) + 1)" in css
    assert 'id="aplicacion-presentacion-fondo" aria-hidden="true"' in plantilla
    assert "tabindex" not in plantilla
    assert "data-movimiento-reducido" in css
