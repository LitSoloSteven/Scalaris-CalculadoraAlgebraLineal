"""Acceso a los modelos matriciales desde el catálogo, el inicio y la barra real."""
import asyncio
from dataclasses import replace

import pytest

from src.frontend.navegacion import consultas, ruta_de
from tests.comun_construccion_vistas import construir_pagina

MODELOS_MATRICIALES = ("leontief", "transformaciones")


@pytest.mark.parametrize("pilar", ["algebra", "utilidades"])
def test_navegacion_cubre_todas_las_herramientas_habilitadas(pilar):
    """Cada herramienta visible tiene un acceso contextual con el orden del catálogo."""
    catalogo = consultas.herramientas_visibles(pilar)
    elementos = consultas.elementos_navegacion(pilar)
    assert tuple(elemento.clave for elemento in elementos) == tuple(
        herramienta.identificador for herramienta in catalogo
    )
    assert tuple(elemento.ruta for elemento in elementos) == tuple(
        herramienta.ruta for herramienta in catalogo
    )


@pytest.mark.parametrize("identificador", MODELOS_MATRICIALES)
def test_modelo_deshabilitado_se_omite_del_menu(monkeypatch, identificador):
    """Deshabilitar un modelo en el catálogo retira solo su acceso contextual."""
    anteriores = consultas.elementos_navegacion("algebra")
    catalogo = tuple(replace(herramienta, habilitada=False)
                     if herramienta.identificador == identificador else herramienta
                     for herramienta in consultas.HERRAMIENTAS)
    monkeypatch.setattr(consultas, "HERRAMIENTAS", catalogo)
    assert consultas.elementos_navegacion("algebra") == tuple(
        elemento for elemento in anteriores if elemento.clave != identificador
    )


def test_inicio_monta_enlaces_para_ambos_modelos(monkeypatch):
    """El directorio permite abrir ambos modelos en sus respectivos grupos."""
    async def comprobar(vista, cliente):
        """Inspecciona los enlaces construidos por la página pública de inicio."""
        enlaces = {elemento._props["data-clave"]: elemento
                   for elemento in cliente.elements.values()
                   if "inicio-enlace" in elemento.classes and "data-clave" in elemento._props}
        for identificador in MODELOS_MATRICIALES:
            assert enlaces[identificador]._props["href"] == ruta_de(identificador)
        assert len(enlaces) == 16
    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


@pytest.mark.parametrize("identificador,seccion,total", [
    ("sistemas", ("sistemas", "metodos_iterativos", "leontief"), 3),
    ("leontief", ("sistemas", "metodos_iterativos", "leontief"), 3),
    ("transformaciones", ("vectores", "transformaciones"), 5),
])
def test_barra_ofrece_modelos_y_marca_solo_la_vista_actual(monkeypatch, identificador, seccion, total):
    """Cada modelo aparece en su sección y tiene estado activo al abrirlo."""
    monkeypatch.setenv("SCALARIS_NAV", "1")

    async def comprobar(vista, cliente):
        """Verifica los destinos de la sección y su selección exclusiva."""
        enlaces = [elemento for elemento in cliente.elements.values() if "navegacion-elemento" in elemento._classes]
        assert len(enlaces) == total
        destinos = {elemento._props["href"] for elemento in enlaces}
        assert {ruta_de(clave) for clave in seccion} <= destinos
        activos = [elemento._props["href"] for elemento in enlaces if elemento._props.get("aria-current") == "page"]
        assert activos == [ruta_de(identificador)]
    asyncio.run(construir_pagina(monkeypatch, identificador, comprobar))
