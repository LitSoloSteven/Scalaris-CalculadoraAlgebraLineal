"""Recorrido integrado del registro real, estructura común y contexto pedagógico."""
import asyncio

import pytest

from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.comun_regla_falsa_vista import captura_regla_falsa
from tests.test_regla_falsa_registro_publico import comprobar_hoja_versionada


@pytest.mark.parametrize("navegacion", ["0", "1"])
def test_ruta_publica_con_cabecera_y_motor_real(monkeypatch, navegacion):
    """La ruta construye controles, enlaces activos y Glosa en ambos modos de navegación."""
    monkeypatch.setitem(VISTAS_RUTAS, "regla_falsa", ("regla_falsa.pagina", "VistaReglaFalsa"))
    monkeypatch.setenv("SCALARIS_NAV", navegacion)

    async def comprobar(vista, cliente):
        """Calcula y revoca un resultado real dentro de la página registrada."""
        comprobar_hoja_versionada(cliente.head_html)
        assert "movimiento_biseccion.js" not in cliente.head_html
        assert vista.panel_ia is not None
        activos = [elemento for elemento in cliente.elements.values()
                   if elemento._props.get("aria-current") == "page"]
        assert activos and any(elemento._props.get("href") == "/utilidades/regla-falsa" for elemento in activos)
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "EXITO"
        assert len(vista.ultimo_resultado["iteraciones"]) == 9
        vista.reproductor_pasos.ir_a(4)
        assert vista.obtener_contexto_ia().herramienta == "regla_falsa"
        assert vista.obtener_contexto_ia().foco.captura.detalle["iteracion"] is vista.ultimo_resultado["iteraciones"][3]
        vista.limpiar_todo()
        assert vista.obtener_contexto_ia().foco is None and vista.ultimo_resultado is None

    asyncio.run(construir_pagina(monkeypatch, "regla_falsa", comprobar))
