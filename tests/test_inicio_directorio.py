"""Pruebas de la portada integrada, su orden de lectura y el ejemplo local."""
import asyncio

import pytest

from src.frontend.navegacion import enlace_elemento_navegacion
from src.frontend.navegacion.secciones_inicio import secciones_inicio
from src.frontend.vistas.inicio.panel_ejemplo import renderizar_panel_ejemplo
from tests.comun_construccion_vistas import construir_pagina


def test_enlaces_respetan_el_orden_de_lectura_del_directorio(monkeypatch):
    """Las secciones mantienen la secuencia natural de enlaces y sus nombres completos."""
    esperado = [
        acceso for seccion in secciones_inicio() for grupo in seccion.grupos for acceso in grupo.accesos
    ]

    async def comprobar(vista, cliente):
        """Compara el árbol de elementos de NiceGUI con el catálogo publicado."""
        directorio = next(elemento for elemento in cliente.elements.values()
                          if "inicio-directorio" in elemento.classes)
        enlaces = [elemento for elemento in directorio.descendants() if "inicio-enlace" in elemento.classes]
        assert len(enlaces) == len(esperado) == 17
        for enlace, acceso in zip(enlaces, esperado, strict=True):
            assert enlace.tag == "a"
            assert "tabindex" not in enlace._props
            assert enlace._props["href"] == enlace_elemento_navegacion(acceso)
            assert enlace._props["data-gesto-inicio"] == acceso.clave
            assert any(getattr(hijo, "content", None) == acceso.etiqueta for hijo in enlace.descendants())

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


def test_destacado_y_ejemplo_comparten_la_ruta_de_sistemas(monkeypatch):
    """El ejemplo contiene los dos estados de la fila y enlaces coherentes."""
    async def comprobar(vista, cliente):
        """Inspecciona la acción principal y la plantilla que compone la portada."""
        destacado = next(elemento for elemento in cliente.elements.values()
                         if "inicio-destacado" in elemento.classes)
        panel = next(elemento for elemento in cliente.elements.values()
                     if "inicio-ejemplo-contenedor" in elemento.classes)
        assert destacado.tag == "a"
        assert destacado._props["href"] == "/algebra-lineal/sistemas"
        assert f'href="{destacado._props["href"]}"' in panel.content
        assert '<button class="inicio-ejemplo-accion" type="button" data-ejemplo-reproducir>' in panel.content
        for expresion in ("x + y = 5", "x − y = 1", "F₂ ← F₂ − F₁", "−2y = −4"):
            assert expresion in panel.content

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


@pytest.mark.parametrize("destino", ["https://ejemplo.invalid", "//ejemplo.invalid", "/\\ejemplo.invalid", "/\nejemplo"])
def test_panel_rechaza_destinos_no_locales(destino):
    """El fragmento de ejemplo admite únicamente una URL relativa al origen."""
    with pytest.raises(ValueError, match="ruta interna"):
        renderizar_panel_ejemplo(destino)
