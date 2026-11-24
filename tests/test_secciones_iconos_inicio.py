"""Contrato del directorio y paridad de los iconos entre superficies."""
import asyncio
from dataclasses import replace
from unittest.mock import Mock
from xml.etree.ElementTree import fromstring

from nicegui import Client, core, ui
import pytest

from src.frontend.componentes.aplicacion.controles.barra_navegacion import crear_barra_navegacion
from src.frontend.componentes.aplicacion.base.iconos import icono_svg
from src.frontend.navegacion import (
    consultas,
    enlace_elemento_navegacion,
    herramienta_por_ruta,
    predeterminado_elemento_clave,
)
from src.frontend.navegacion.secciones_inicio import secciones_inicio
from tests.comun_construccion_vistas import construir_pagina


_DESTINOS = (
    ("sistemas", "/algebra-lineal/sistemas", "sistemas_lineales"),
    ("metodos_iterativos", "/algebra-lineal/metodos-iterativos", "metodos_iterativos"),
    ("leontief", "/algebra-lineal/leontief", "leontief"),
    ("matrices", "/algebra-lineal/matrices", "operaciones_matrices"),
    ("inversa", "/algebra-lineal/inversa", "matriz_inversa"),
    ("determinantes", "/algebra-lineal/determinantes", "determinantes"),
    ("factorizacion_lu", "/algebra-lineal/factorizacion-lu", "factorizacion_lu"),
    ("vectores", "/algebra-lineal/vectores", "vectores"),
    ("espacios_subespacios", "/algebra-lineal/espacios-subespacios", "espacios_subespacios"),
    ("transformaciones", "/algebra-lineal/transformaciones", "transformaciones"),
    ("vis:rectas-planos", "/visualizador?escena=rectas-planos", "escena_rectas_planos"),
    ("vis:vectores", "/visualizador?escena=vectores", "escena_vectores"),
    ("vis:combinacion", "/visualizador?escena=combinacion", "escena_combinacion"),
    ("metodos_cerrados", "/utilidades/metodos-cerrados", "metodos_cerrados"),
    ("metodos_abiertos", "/utilidades/metodos-abiertos", "metodos_abiertos"),
    ("bases", "/utilidades/bases", "conversor_bases"),
    ("romanos", "/utilidades/romanos", "romanos"),
)


def _contiene_svg(enlace, nombre_icono):
    """Indica si el enlace contiene el SVG original del catálogo."""
    esperado = icono_svg(nombre_icono)
    return any(getattr(hijo, "content", None) == esperado for hijo in enlace.descendants())


def test_secciones_respetan_orden_subtitulos_y_destinos():
    """Las cinco secciones proyectan los accesos canónicos sin duplicados."""
    secciones = secciones_inicio()
    assert [seccion.titulo for seccion in secciones] == [
        "Sistemas lineales", "Matrices", "Vectores y geometría",
        "Métodos numéricos", "Sistemas de numeración",
    ]
    assert [
        [(grupo.subtitulo, len(grupo.accesos)) for grupo in seccion.grupos]
        for seccion in secciones
    ] == [[(None, 3)], [(None, 4)], [(None, 3), ("Visualizador geométrico", 3)],
          [("Raíces de ecuaciones", 2)], [(None, 2)]]
    accesos = [acceso for seccion in secciones for grupo in seccion.grupos for acceso in grupo.accesos]
    assert tuple((acceso.clave, enlace_elemento_navegacion(acceso), acceso.icono) for acceso in accesos) == _DESTINOS
    assert all(herramienta_por_ruta(acceso.ruta).habilitada for acceso in accesos)
    assert accesos[3].etiqueta == "Operaciones con matrices"
    assert accesos[9].etiqueta == "Transformaciones lineales"


def test_svg_del_directorio_son_distintos_y_decorativos():
    """Cada acceso tiene un símbolo válido con el color heredado del enlace."""
    simbolos = {icono_svg(icono) for _, _, icono in _DESTINOS}
    assert len(simbolos) == len(_DESTINOS)
    for simbolo in simbolos:
        svg = fromstring(simbolo)
        assert svg.tag == "{http://www.w3.org/2000/svg}svg"
        assert svg.get("aria-hidden") == "true"
        assert svg.get("stroke") == "currentColor"
        assert len(svg) > 0


def test_directorio_omite_grupos_y_secciones_sin_accesos(monkeypatch):
    """Las herramientas deshabilitadas y sus escenas no dejan encabezados vacíos."""
    deshabilitadas = {"visualizador", "bases", "romanos"}
    herramientas = tuple(
        replace(herramienta, habilitada=False) if herramienta.identificador in deshabilitadas else herramienta
        for herramienta in consultas.HERRAMIENTAS
    )
    monkeypatch.setattr(consultas, "HERRAMIENTAS", herramientas)
    secciones = {seccion.identificador: seccion for seccion in secciones_inicio()}
    assert "sistemas-numeracion" not in secciones
    grupo, = secciones["vectores-geometria"].grupos
    assert grupo.subtitulo is None
    assert [acceso.clave for acceso in grupo.accesos] == ["vectores", "espacios_subespacios", "transformaciones"]


def test_inicio_publico_muestra_los_svg_del_catalogo(monkeypatch):
    """La portada usa los mismos destinos y símbolos que la proyección."""
    async def comprobar(vista, cliente):
        """Inspecciona los enlaces generados por la página pública de inicio."""
        for _, destino, icono in _DESTINOS:
            enlaces = [elemento for elemento in cliente.elements.values() if elemento._props.get("href") == destino]
            assert any(_contiene_svg(enlace, icono) for enlace in enlaces), destino

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


@pytest.mark.parametrize("claves,ruta", [(None, "/algebra-lineal/leontief"),
                                         ({"sistemas", "metodos_iterativos", "leontief"}, "/algebra-lineal/leontief"),
                                         ({"metodos_cerrados", "metodos_abiertos"}, "/utilidades/metodos-abiertos")])
def test_barra_comparte_svg_de_herramientas(monkeypatch, claves, ruta):
    """Cada barra construye sus accesos desde los símbolos del directorio."""
    monkeypatch.setenv("SCALARIS_NAV", "0" if claves is None else "1")
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-iconos-barra"))
    try:
        with cliente:
            crear_barra_navegacion(ruta_activa=ruta)
        destinos = {elemento._props["href"]: elemento for elemento in cliente.elements.values()
                    if "href" in elemento._props}
        for clave, destino, icono in _DESTINOS:
            if not clave.startswith("vis:") and (claves is None or clave in claves):
                enlace = destinos[destino]
                assert enlace._props["aria-label"] == herramienta_por_ruta(destino).nombre
                assert _contiene_svg(enlace, icono)
        assert destinos[ruta]._props["aria-current"] == "page"
    finally:
        cliente.delete()


@pytest.mark.parametrize("escena", ["rectas-planos", "vectores", "combinacion"])
def test_barra_contextual_marca_y_revela_cada_escena(monkeypatch, escena):
    """Solo la escena activa tiene aria-current y se solicita mostrarla al conectar."""
    monkeypatch.setenv("SCALARIS_NAV", "1")
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-iconos-escena"))
    enviar = Mock()
    monkeypatch.setattr(cliente, "run_javascript", enviar)
    try:
        with cliente:
            crear_barra_navegacion(ruta_activa="/visualizador", clave_activa=f"vis:{escena}")
        enlaces = {elemento._props["href"]: elemento for elemento in cliente.elements.values()
                   if "navegacion-elemento" in elemento.classes}
        destinos_seccion = {destino: icono for clave, destino, icono in _DESTINOS
                            if clave.startswith("vis:")}
        assert enlaces.keys() == destinos_seccion.keys()
        for destino, icono in destinos_seccion.items():
            assert enlaces[destino]._props["aria-label"]
            assert _contiene_svg(enlaces[destino], icono)
        activos = [destino for destino, enlace in enlaces.items() if enlace._props.get("aria-current") == "page"]
        assert activos == [f"/visualizador?escena={escena}"]
        assert not enviar.called
        cliente.connect_handlers[0]()
        enviar.assert_any_call("window.scalaris?.navegacion?.centrarActivo?.();")
    finally:
        cliente.delete()


@pytest.mark.parametrize("alias,clave,canonica", [
    ("/utilidades/biseccion", "metodos_cerrados", "/utilidades/metodos-cerrados"),
    ("/utilidades/regla-falsa", "metodos_cerrados", "/utilidades/metodos-cerrados"),
    ("/algebra-lineal/matrices?operacion=determinante", "determinantes", "/algebra-lineal/determinantes"),
])
def test_alias_conserva_su_referencia_canonica(alias, clave, canonica):
    """Los accesos heredados mantienen su herramienta canónica en navegación."""
    assert herramienta_por_ruta(alias).ruta == canonica
    assert predeterminado_elemento_clave(alias) == clave
