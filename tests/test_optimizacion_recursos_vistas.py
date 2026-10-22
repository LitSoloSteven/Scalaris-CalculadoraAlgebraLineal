"""Selección, orden de dependencias y huellas de los recursos servidos por página."""
import asyncio
import hashlib
import re
from pathlib import Path

import pytest

from src.frontend import tema, versionado_recursos
from src.frontend.recursos_vistas import seleccionar_recursos
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina

_RECURSOS = Path("src/frontend/recursos")
_URL = re.compile(r'(?:src|href)="(/assets/[^"?]+)(?:\?v=([a-f0-9]+))?"')


@pytest.mark.parametrize("vista", VISTAS_RUTAS)
def test_paginas_versionan_cabecera_sin_cambiar_recursos_de_componentes(monkeypatch, vista):
    """Las rutas versionan recursos globales y conservan las etiquetas contractuales de captura."""
    async def comprobar(instancia, cliente):
        """Inspecciona recursos, huellas y orden de dependencias en el cliente construido."""
        cabecera = cliente.head_html
        recursos = _URL.findall(cabecera)
        assert recursos
        globales = {url for url, _ in _URL.findall(tema._CABECERA_HTML + tema._CABECERA_GLOSA_HTML)}
        for url, version in recursos:
            contenido = (_RECURSOS / url.removeprefix("/assets/")).read_bytes()
            assert version == (hashlib.sha256(contenido).hexdigest() if url in globales else "")
        assert cabecera.index("inicializacion_tema.js") < cabecera.index("/assets/css/")
        assert cabecera.index("observacion_dom.js") < cabecera.index("selector_tema.js")
        assert cabecera.index("interacciones_globales.js") < cabecera.index("cuadricula_compartida.js")
        assert cabecera.index("escritura_progresiva.js") < cabecera.index("reproductor_pasos.js")
        assert ("inicio.js" in cabecera) == (vista == "inicio")
        assert ("tema_graficos.js" in cabecera) == (vista == "visualizador")
        assert ("sincronizacion_diseno.js" in cabecera) == (vista == "visualizador")
        assert ("sistemas_metodo.js" in cabecera) == (vista == "sistemas")
        assert "MathJax-script" in cabecera

    asyncio.run(construir_pagina(monkeypatch, vista, comprobar))


def test_seleccion_conserva_plantillas_recursos_desconocidos_y_orden():
    """La selección deja el contrato universal intacto y no altera etiquetas ajenas."""
    cabecera = tema._CABECERA_HTML
    assert seleccionar_recursos(cabecera, "") == cabecera
    assert seleccionar_recursos(cabecera, "desconocida") == cabecera
    ajena = '<script src="/assets/js/futuro.js"></script>'
    assert seleccionar_recursos(ajena, "inicio") == ajena
    seleccion = seleccionar_recursos(cabecera, "visualizador")
    assert "vistas_vectores.css" in seleccion
    assert "vistas_geometria.css" in seleccion
    assert "vistas_inicio_matriz.css" not in seleccion
    assert "vistas_modelos.css" in seleccionar_recursos(cabecera, "determinantes")
    for vista in ("sistemas", "inversa", "visualizador"):
        assert "vistas_inicio_adaptable.css" in seleccionar_recursos(cabecera, vista)
    for vista in ("matrices", "vectores", "leontief", "transformaciones", "bases", "romanos"):
        assert "vistas_inicio_adaptable.css" not in seleccionar_recursos(cabecera, vista)


def test_versionado_es_idempotente_y_no_reescribe_entradas_ajenas():
    """Solo URL propias conocidas reciben una huella; consultas y rutas ajenas se conservan."""
    cabecera = '<script src="/assets/js/tema.js"></script>'
    versionada = versionado_recursos.versionar_html(cabecera)
    assert versionada != cabecera
    assert versionado_recursos.versionar_html(versionada) == versionada
    for url in ("https://externo/js/tema.js", "/assets/js/../tema.js", "/assets/js/ausente.js",
                "/assets/js/tema.js?x=1", "/assets/css/tema.js"):
        etiqueta = f'<script src="{url}"></script>'
        assert versionado_recursos.versionar_html(etiqueta) == etiqueta


def test_huellas_cambian_solo_con_el_contenido(monkeypatch):
    """Dos despliegues del mismo contenido comparten URL y un cambio invalida la caché."""
    versiones = versionado_recursos._calcular_versiones()
    assert versiones == versionado_recursos._calcular_versiones()
    leer = Path.read_bytes

    def leer_cambio(ruta):
        """Simula un cambio de contenido sin escribir archivos de prueba."""
        return leer(ruta) + (b" " if ruta.name == "tema.js" else b"")

    monkeypatch.setattr(Path, "read_bytes", leer_cambio)
    nuevas = versionado_recursos._calcular_versiones()
    assert [url for url in versiones if versiones[url] != nuevas[url]] == ["/assets/js/tema.js"]
