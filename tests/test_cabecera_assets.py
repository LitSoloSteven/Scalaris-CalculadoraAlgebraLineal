"""Plantillas de cabecera, configuración de figuras y orden de carga."""
import json
import re

from src.frontend import tema
from tests.comun import RAIZ, ARCHIVOS_CSS


def test_cabecera_carga_estilos_en_orden_de_cascada():
    """La plantilla incluye exactamente las hojas declaradas y en su orden."""
    nombres = re.findall(r'<link rel="stylesheet" href="/assets/css/([^"]+)"', tema._CABECERA_HTML)
    assert nombres == [ruta.name for ruta in ARCHIVOS_CSS]


def test_configuracion_graficos_es_datos_json():
    """El bloque declarativo conserva las cuatro paletas y no ejecuta código."""
    coincidencia = re.search(
        r'<script id="scalaris-configuracion-graficos" type="application/json">(.*?)</script>',
        tema._CABECERA_HTML,
    )
    assert coincidencia
    datos = json.loads(coincidencia.group(1))
    assert datos == {
        "paletas": tema.PALETAS_POR_TEMA, "solucion": tema.COLORES_SOLUCION_POR_TEMA,
        "texto": tema.COLORES_TEXTO_GRAFICOS, "cuadricula": tema.COLORES_CUADRICULA_GRAFICOS,
    }


def test_scripts_de_cabecera_son_assets_existentes():
    """Los scripts ejecutables se cargan desde assets; solo JSON queda embebido."""
    cabecera = tema._CABECERA_HTML + tema._CABECERA_GLOSA_HTML
    scripts = re.findall(r'<script([^>]*)>(.*?)</script>', cabecera, re.DOTALL)
    assert scripts
    for atributos, contenido in scripts:
        if 'type="application/json"' in atributos:
            continue
        assert contenido.strip() == ""
        origen = re.search(r'src="([^"]+)"', atributos)
        assert origen
        if origen.group(1).startswith("/assets/"):
            assert (RAIZ / "src/frontend" / origen.group(1).lstrip("/")).is_file()


def test_inicializacion_precede_estilos_y_consumidores():
    """El tema se prepara antes de CSS y Glosa antes de sus interacciones."""
    cabecera = tema._CABECERA_HTML
    assert cabecera.index('scalaris-configuracion-graficos') < cabecera.index('/assets/js/inicializacion_tema.js')
    assert cabecera.index('/assets/js/inicializacion_tema.js') < cabecera.index('<link rel="stylesheet"')
    assert cabecera.index('/assets/js/tema.js') > cabecera.index('/assets/css/reproductor_pasos.css')
    glosa = tema._CABECERA_GLOSA_HTML
    assert glosa.index('/assets/js/inicializacion_glosa.js') < glosa.index('/assets/js/glosa_dock.js')
