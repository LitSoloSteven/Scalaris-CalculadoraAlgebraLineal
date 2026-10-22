"""Descubrimiento de fuentes cliente externas y embebidas para medirlas juntas."""
from html.parser import HTMLParser

from tests.comun import RAIZ
from tests.comun_integridad_cliente import fragmentos_python

TIPOS_JAVASCRIPT = {
    "", "module", "text/javascript", "application/javascript",
    "text/ecmascript", "application/ecmascript",
}


class LectorCodigoHTML(HTMLParser):
    """Recoge cuerpos ejecutables de código cliente y su línea original, sin ejecutarlos."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.fragmentos = []
        self._partes = None
        self._linea = 1

    def handle_starttag(self, tag, attrs):
        """Inicia la lectura de un código cliente JavaScript sin recurso externo."""
        if tag != "script":
            return
        atributos = dict(attrs)
        tipo = (atributos.get("type") or "").strip().lower()
        if "src" not in atributos and tipo in TIPOS_JAVASCRIPT:
            self._partes = []
            self._linea = self.getpos()[0]

    def handle_data(self, datos):
        """Conserva el texto y los saltos de línea del cuerpo ejecutable."""
        if self._partes is not None:
            self._partes.append(datos)

    def handle_endtag(self, tag):
        """Finaliza un cuerpo ejecutable conservando también código cliente vacíos."""
        if tag == "script" and self._partes is not None:
            self.fragmentos.append((self._linea, "".join(self._partes)))
            self._partes = None


def fuentes_javascript(rutas):
    """Devuelve archivos JS y cuerpos de HTML/Python con procedencia verificable."""
    fuentes = [_fuente(ruta, 1, ruta.read_text(encoding="utf-8"), "archivo")
               for ruta in rutas if ruta.suffix == ".js"]
    for ruta in rutas:
        if ruta.suffix == ".html":
            fuentes.extend(_codigo_html(ruta))
    rutas_python = [ruta for ruta in rutas if ruta.suffix == ".py"]
    fuentes.extend(_fuente(RAIZ / ruta, linea, contenido, "python")
                   for ruta, linea, contenido in fragmentos_python(rutas_python, solo_emisiones=True))
    fuentes.extend(_codigo_html_python(rutas_python))
    return fuentes


def _codigo_html(ruta):
    lector = LectorCodigoHTML()
    lector.feed(ruta.read_text(encoding="utf-8"))
    lector.close()
    return [_fuente(ruta, linea, contenido, "html")
            for linea, contenido in lector.fragmentos]


def _codigo_html_python(rutas):
    fragmentos = fragmentos_python(rutas, solo_emisiones=True, emisores=("add_head_html", "add_body_html", "html"))
    fuentes = []
    for ruta, linea, contenido in fragmentos:
        lector = LectorCodigoHTML()
        lector.feed(contenido)
        lector.close()
        fuentes.extend(_fuente(RAIZ / ruta, linea + inicio - 1, codigo, "html")
                       for inicio, codigo in lector.fragmentos)
    return fuentes


def _fuente(ruta, linea, contenido, origen):
    """La línea Python identifica la emisión; HTML/JS identifican el cuerpo del recurso."""
    return {"ruta": ruta.relative_to(RAIZ).as_posix(), "linea": linea,
            "contenido": contenido, "origen": origen}
