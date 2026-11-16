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
    """El inicio real permite abrir los dos modelos desde sus tarjetas de Álgebra."""
    async def comprobar(vista, cliente):
        """Inspecciona los enlaces construidos por la página pública de inicio."""
        tarjetas = {elemento._props.get("data-clave"): elemento
                    for elemento in cliente.elements.values() if "inicio-tarjeta" in elemento._classes}
        for identificador in MODELOS_MATRICIALES:
            assert tarjetas[identificador]._props["href"] == ruta_de(identificador)
        assert len(tarjetas) == 16
    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


@pytest.mark.parametrize("identificador", ["sistemas", *MODELOS_MATRICIALES])
def test_barra_ofrece_modelos_y_marca_solo_la_vista_actual(monkeypatch, identificador):
    """Los modelos aparecen en las vistas de Álgebra y tienen estado activo al abrirlos."""
    monkeypatch.setenv("SCALARIS_NAV", "1")

    async def comprobar(vista, cliente):
        """Verifica rutas de ambos modelos y la selección exclusiva en la barra montada."""
        enlaces = [elemento for elemento in cliente.elements.values() if "navegacion-elemento" in elemento._classes]
        assert len(enlaces) == 8
        destinos = {elemento._props["href"] for elemento in enlaces}
        assert {ruta_de(modelo) for modelo in MODELOS_MATRICIALES} <= destinos
        activos = [elemento._props["href"] for elemento in enlaces if elemento._props.get("aria-current") == "page"]
        assert activos == [ruta_de(identificador)]
    asyncio.run(construir_pagina(monkeypatch, identificador, comprobar))
