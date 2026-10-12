"""Barridos estáticos de estilos, fórmulas y accesibilidad de controles."""
import re
import ast
from tests.comun_javascript import leer_interacciones_cliente
from tests.comun_recorrido_codigo import recorrer_archivos_codigo, recorrer_lineas_codigo

CARPETA_INTERFAZ = 'src/frontend'
EXTENSIONES_PRESENTACION = ('.py', '.js', '.css')


def _archivos_presentacion_sin_splash():
    return (ruta for ruta in recorrer_archivos_codigo([CARPETA_INTERFAZ], EXTENSIONES_PRESENTACION)
            if ruta.name != 'splash.js')


def test_interfaz_sin_altura_estatica_pantalla():
    """Ningún archivo de la interfaz contiene altura estática de pantalla."""
    infracciones = []
    rutas = recorrer_archivos_codigo([CARPETA_INTERFAZ], EXTENSIONES_PRESENTACION)
    for ruta, numero, linea in recorrer_lineas_codigo(rutas):
        if '100vh' in linea:
            infracciones.append(f"{ruta}:{numero} -> {linea.strip()}")
    assert not infracciones, "Se encontraron referencias a 100vh:\n" + "\n".join(infracciones)


def test_interfaz_sin_filtros_de_desenfoque():
    """La interfaz evita filtros de desenfoque fuera del splash."""
    infracciones = []
    for ruta, numero, linea in recorrer_lineas_codigo(_archivos_presentacion_sin_splash()):
        if 'backdrop-filter' in linea or 'blur(' in linea:
            infracciones.append(f"{ruta}:{numero} -> {linea.strip()}")
    assert not infracciones, "Se encontraron 'backdrop-filter' o 'blur(' fuera de splash.js:\n" + "\n".join(infracciones)


def test_css_sin_colores_literales_fuera_de_tokens():
    """Las hojas de estilos usan tokens para sus colores."""
    from tests.comun import ARCHIVOS_CSS
    patron_color = re.compile(r'(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\))')
    infracciones = []
    for archivo in ARCHIVOS_CSS:
        if archivo.name == "tokens.css":
            continue
        lineas = archivo.read_text(encoding="utf-8").splitlines()
        for i, linea in enumerate(lineas, 1):
            limpia = linea.split('/*')[0].strip()
            coincidencias = patron_color.findall(limpia)
            if coincidencias:
                infracciones.append(f"{archivo.name}:{i} -> {limpia} (colores: {coincidencias})")

    assert not infracciones, "Colores literales encontrados fuera de tokens.css:\n" + "\n".join(infracciones)


def test_interfaz_sin_capas_numericas_elevadas():
    """Las capas locales no superan diez y la capa modal usa su token."""
    infracciones = []
    patron_profundidad = re.compile(r'z-index\s*:\s*([0-9]+)', re.IGNORECASE)
    for ruta, numero, linea in recorrer_lineas_codigo(_archivos_presentacion_sin_splash()):
        coincidencia = patron_profundidad.search(linea)
        if coincidencia and int(coincidencia.group(1)) > 10:
            infracciones.append(f"{ruta}:{numero} -> z-index: {int(coincidencia.group(1))}")
    interacciones = leer_interacciones_cliente()
    assert "9999" not in interacciones, "Las interacciones globales contienen profundidad literal"
    assert "var(--z-modal)" in interacciones, "Las interacciones globales deben usar el token de profundidad"
    assert not infracciones, "z-index numéricos elevados no permitidos:\n" + "\n".join(infracciones)


def _infracciones_formulas(ruta, contenido):
    objetivo = chr(36) + chr(36)
    lineas = contenido.splitlines()
    infracciones = []
    for numero, linea in enumerate(lineas, 1):
        if objetivo in linea:
            ventana = '\n'.join(lineas[max(0, numero - 10):min(len(lineas), numero + 10)])
            if 'math-scroll-container' not in ventana:
                infracciones.append(f"{ruta}:{numero} -> {linea.strip()}")
    return infracciones


def test_formulas_tienen_contenedor_desplazable():
    """Las fórmulas de vistas y componentes disponen de su contenedor."""
    infracciones = []
    for ruta in recorrer_archivos_codigo([CARPETA_INTERFAZ], ('.py',)):
        carpeta = str(ruta.parent)
        if 'vistas' not in carpeta and 'componentes' not in carpeta:
            continue
        infracciones.extend(_infracciones_formulas(ruta, ruta.read_text(encoding='utf-8')))
    assert not infracciones, "Fórmulas $$ fuera de math-scroll-container:\n" + "\n".join(infracciones)


def _es_boton_icono_sin_texto(nodo):
    if not isinstance(nodo, ast.Call) or not isinstance(nodo.func, ast.Attribute):
        return False
    if nodo.func.attr != 'button':
        return False
    tiene_texto = bool(nodo.args and _texto_posicional_no_vacio(nodo.args[0]))
    tiene_icono = any(clave.arg == 'icon' for clave in nodo.keywords)
    return not tiene_texto and tiene_icono


def _texto_posicional_no_vacio(nodo):
    return isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and nodo.value.strip() != ''


def _infracciones_botones(ruta, contenido):
    try:
        arbol = ast.parse(contenido, filename=str(ruta))
    except Exception:
        return []
    lineas = contenido.splitlines()
    infracciones = []
    for nodo in ast.walk(arbol):
        if _es_boton_icono_sin_texto(nodo):
            fragmento = '\n'.join(lineas[nodo.lineno - 1:nodo.end_lineno + 3])
            if 'aria-label' not in fragmento:
                infracciones.append(f"{ruta}:{nodo.lineno} -> {fragmento[:100]}")
    return infracciones


def test_botones_icono_tienen_nombre_accesible():
    """Todo botón con icono y sin texto accesible tiene aria-label."""
    infracciones = []
    for ruta in recorrer_archivos_codigo([CARPETA_INTERFAZ], ('.py',)):
        infracciones.extend(_infracciones_botones(ruta, ruta.read_text(encoding='utf-8')))
    assert not infracciones, "Botones de solo icono sin aria-label:\n" + "\n".join(infracciones)
