"""Contrato público de navegación y recursos exclusivos de la herramienta de secantes."""
import hashlib
import re
from pathlib import Path

import pytest

from src.frontend import tema
from src.frontend.navegacion import (
    ORDEN_NAVEGACION_PLANA, elementos_navegacion, herramienta_por_identificador,
    herramienta_por_ruta, herramientas_visibles, ruta_de, ruta_navegacion,
)
from src.frontend.recursos_vistas import seleccionar_recursos


def test_registro_visible_con_identidad_ruta_y_contexto_coherentes():
    """El catálogo alimenta inicio, navegación clásica, pilares y migas con una identidad única."""
    herramienta = herramienta_por_identificador("regla_falsa")
    assert herramienta.habilitada and herramienta in herramientas_visibles("utilidades")
    assert ruta_de("regla_falsa") == "/utilidades/regla-falsa"
    assert herramienta_por_ruta(herramienta.ruta + "/?origen=inicio") is herramienta
    assert ORDEN_NAVEGACION_PLANA.count("regla_falsa") == 1
    elementos = [elemento for elemento in elementos_navegacion("utilidades")
                 if elemento.identificador_herramienta == "regla_falsa"]
    assert len(elementos) == 1 and elementos[0].etiqueta_corta == "Regla falsa"
    assert ruta_navegacion(herramienta.ruta)[-1] == (herramienta.nombre, herramienta.ruta)


@pytest.mark.parametrize("vista", ["regla_falsa", "biseccion", "inicio", "sistemas", "visualizador"])
def test_recursos_de_raices_no_filtran_movimiento_a_otras_herramientas(vista):
    """La página de secantes comparte tema y reproductor sin cargar los scripts propios de bisección."""
    cabecera = tema._CABECERA_HTML + tema._CABECERA_REGLA_FALSA_HTML
    seleccion = seleccionar_recursos(cabecera, vista)
    assert ("vistas_regla_falsa.css" in seleccion) == (vista == "regla_falsa")
    assert ("vistas_biseccion.css" in seleccion) == (vista == "biseccion")
    for nombre in ("grafico_biseccion", "movimiento_biseccion", "banda_biseccion", "paso_biseccion"):
        assert (nombre + ".js" in seleccion) == (vista == "biseccion")
    assert ("tema_graficos.js" in seleccion) == (vista in {"regla_falsa", "biseccion", "visualizador"})
    assert "reproductor_pasos.js" in seleccion and "MathJax-script" in seleccion
    assert ("captura_pdf.js" in seleccion) == (vista in {"sistemas", "visualizador"})


def comprobar_hoja_versionada(cabecera):
    """Contrasta la hoja realmente cargada con su contenido y el orden de cascada común."""
    versiones = re.findall(r'/assets/css/vistas_regla_falsa.css\?v=([a-f0-9]+)', cabecera)
    contenido = Path("src/frontend/recursos/css/vistas_regla_falsa.css").read_bytes()
    assert versiones == [hashlib.sha256(contenido).hexdigest()]
    assert cabecera.index("vistas_inversa.css") < cabecera.index("vistas_regla_falsa.css")
