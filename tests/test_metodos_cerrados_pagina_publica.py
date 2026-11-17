"""Contrato de los tres accesos públicos a la vista común de raíces."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.controladores.inicio._recientes import normalizar_recientes
from src.frontend.navegacion import predeterminado_elemento_clave, ruta_de, ruta_navegacion
from src.frontend.vistas.metodos_cerrados.vista_metodos_cerrados import VistaMetodosCerrados
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.test_metodos_cerrados_calculo import captura_ejercicio
from tests.test_metodos_cerrados_exploracion import _buscar, _resolver_lote
from tests.test_regla_falsa_registro_publico import comprobar_hoja_versionada

ACCESOS = (
    ("metodos_cerrados", "biseccion", ("metodos_cerrados.vista_metodos_cerrados", "VistaMetodosCerrados")),
    ("biseccion", "biseccion", ("metodos_cerrados.vista_metodos_cerrados", "VistaMetodosCerrados")),
    ("regla_falsa", "regla_falsa", ("regla_falsa.pagina", "VistaReglaFalsa")),
)


def test_recientes_de_inicio_consolidan_los_identificadores_anteriores():
    """Conserva el orden y una sola tarjeta para ambos identificadores guardados."""
    recientes = normalizar_recientes(["regla_falsa", "bases", "biseccion", "metodos_cerrados", "romanos"])
    assert [herramienta.identificador for herramienta in recientes] == ["metodos_cerrados", "bases", "romanos"]


@pytest.mark.parametrize("identificador,metodo,montaje", ACCESOS)
def test_accesos_publicos_comparten_identidad_recursos_y_grafica(monkeypatch, identificador, metodo, montaje):
    """Valida la navegación, el cálculo y la exploración desde cada acceso real."""
    monkeypatch.setitem(VISTAS_RUTAS, identificador, montaje)
    monkeypatch.setenv("SCALARIS_NAV", "1")

    async def comprobar(vista, cliente):
        """Comprueba la misma vista y ejecuta búsqueda y lote con el método inicial."""
        assert isinstance(vista, VistaMetodosCerrados)
        assert vista.capturar()["metodo"] == metodo
        comprobar_hoja_versionada(cliente.head_html)
        assert "estructura_metodos_raices.css?v=" in cliente.head_html
        assert "tema_graficos.js?v=" in cliente.head_html
        for recurso in ("vistas_biseccion.css", "vistas_regla_falsa.css", "vistas_metodos_abiertos.css",
                        "grafico_biseccion.js", "captura_pdf.js"):
            assert recurso not in cliente.head_html
        ruta = ruta_de(identificador)
        canonica = ruta_de("metodos_cerrados")
        assert predeterminado_elemento_clave(ruta) == "metodos_cerrados"
        assert ruta_navegacion(ruta)[-1] == ("Métodos cerrados", canonica)
        activos = [elemento._props.get("href") for elemento in cliente.elements.values()
                   if elemento._props.get("aria-current") == "page"]
        assert activos == [canonica]
        await _comprobar_calculo_y_lote(vista, cliente, metodo)

    asyncio.run(construir_pagina(monkeypatch, identificador, comprobar))


async def _comprobar_calculo_y_lote(vista, cliente, metodo):
    grafica = vista.grafica.nodo
    vista.cargar_captura(captura_ejercicio("(x+1)*(x-1)*(x-2)", "0.5", "1.5", "radianes"))
    await vista.resolver()
    assert vista.ultimo_resultado["estado"] == "EXITO"
    assert vista.obtener_contexto_ia().herramienta == metodo
    lote = await _buscar(vista, cliente)
    await _resolver_lote(lote, metodo)
    assert lote.respuesta["resultados"]
    assert [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.plotly)] == [grafica]
