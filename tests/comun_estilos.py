"""Lectura de tokens, bloques CSS y cálculo de contraste para las pruebas."""
import re
from pathlib import Path

from tests.comun import ARCHIVOS_CSS


def _seleccionar_tema(selector, temas):
    for tema in ("marea", "medianoche", "papel"):
        if f'data-theme="{tema}"' in selector:
            return tema
    if selector.strip() == ":root" and not temas["papel"]:
        return "papel"
    return None


def _declaraciones_tokens(cuerpo):
    tokens = {}
    for declaracion in cuerpo.split(";"):
        if ":" not in declaracion:
            continue
        nombre, valor = declaracion.strip().split(":", 1)
        if nombre.strip().startswith("--"):
            tokens[nombre.strip()] = valor.strip().split("/*")[0].strip()
    return tokens


def extraer_clases_semanticas(contenido, patron):
    """Recoge nombres semánticos coincidentes con un patrón de clases HTML o Python."""
    clases = set()
    for coincidencia in re.findall(patron, contenido):
        for palabra in coincidencia.split():
            nombre = re.sub(r'[^a-zA-Z0-9_-]', '', palabra)
            if any(nombre.startswith(prefijo) for prefijo in ('nav-', 'hub-', 'glosa-')):
                clases.add(nombre)
    return clases


def analizar_tokens(ruta, pasadas=6, exigir_cierre=True):
    """Extrae los tres temas y resuelve referencias según el lector original."""
    contenido = Path(ruta).read_text(encoding="utf-8")
    temas = {"papel": {}, "marea": {}, "medianoche": {}}
    for selector, cuerpo in re.findall(r"(:root[^{]*)\{([^}]+)\}", contenido, re.DOTALL):
        tema = _seleccionar_tema(selector, temas)
        if tema:
            temas[tema].update(_declaraciones_tokens(cuerpo))
    for tokens in temas.values():
        for _ in range(pasadas):
            _resolver_referencias(tokens, exigir_cierre)
    return temas


def _resolver_referencias(tokens, exigir_cierre):
    for nombre, valor in list(tokens.items()):
        if valor.startswith("var(") and (not exigir_cierre or valor.endswith(")")):
            referencia = valor[4:-1].strip()
            if referencia in tokens:
                tokens[nombre] = tokens[referencia]


def hexadecimal_a_rgb(codigo, limpiar_espacios=True):
    """Convierte un hexadecimal de seis cifras a componentes RGB normalizadas."""
    codigo = codigo.lstrip("#")
    if limpiar_espacios:
        codigo = codigo.strip()
    return tuple(int(codigo[indice:indice + 2], 16) / 255.0 for indice in (0, 2, 4))


def luminancia_relativa(rgb):
    """Calcula la luminancia relativa con la transferencia definida por WCAG."""
    def canal(valor):
        return valor / 12.92 if valor <= 0.04045 else ((valor + 0.055) / 1.055) ** 2.4

    rojo, verde, azul = [canal(valor) for valor in rgb]
    return 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul


def razon_contraste(primer_rgb, segundo_rgb):
    """Devuelve la razón WCAG entre dos colores, independiente de su orden."""
    primera = luminancia_relativa(primer_rgb)
    segunda = luminancia_relativa(segundo_rgb)
    return (max(primera, segunda) + 0.05) / (min(primera, segunda) + 0.05)


def leer_css_hub():
    """Lee las hojas del Hub respetando el orden de la cascada de pruebas."""
    return "\n".join(
        ruta.read_text(encoding="utf-8") for ruta in ARCHIVOS_CSS
        if ruta.name.startswith("vistas_hub_")
    )


def buscar_cierre_bloque(css, apertura):
    """Localiza la llave de cierre de un bloque CSS con bloques anidados."""
    profundidad = 0
    for indice in range(apertura, len(css)):
        if css[indice] == "{":
            profundidad += 1
        elif css[indice] == "}":
            profundidad -= 1
            if profundidad == 0:
                return indice
    raise AssertionError("Bloque CSS sin cerrar")


def bloque_css(css, selector):
    """Extrae el cuerpo del primer bloque del selector, incluidas sus reglas."""
    inicio = css.index(selector)
    apertura = css.index("{", inicio)
    return css[apertura + 1:buscar_cierre_bloque(css, apertura)]
