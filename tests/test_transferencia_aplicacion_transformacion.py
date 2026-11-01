"""Transferencia de A vigente sin exportar coordenadas con una semántica distinta."""
import asyncio

import pytest

from src.frontend.componentes import acciones_matriz
from src.frontend.controladores.destinos_matriz import destinos_compatibles
from src.frontend.vistas.operaciones_matrices._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("rectangular", [False, True])
def test_transferencia_solo_envia_A_y_rechaza_eventos_obsoletos(monkeypatch, rectangular):
    """Los destinos respetan dimensiones; un evento retenido no transfiere tras editar."""
    async def comprobar(vista, cliente):
        """Invoca el manejador real con transporte de transferencia aislado."""
        guardados, navegados = [], []
        monkeypatch.setattr(acciones_matriz, "guardar_matriz", lambda origen, datos: guardados.append(datos) or "token")
        monkeypatch.setattr(acciones_matriz.ui.navigate, "to", navegados.append)
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        if rectangular:
            vista._aplicar_dimension("filas", 3)
        await vista._analizar(vista.boton_calcular)
        botones = [elemento for elemento in vista.contenedor_resultados.descendants()
                   if "data-destino-matriz" in elemento._props]
        assert {boton._props["data-destino-matriz"] for boton in botones} == set(
            destinos_compatibles(vista.filas, vista.columnas, "transformaciones"))
        accion = next(escucha.handler for escucha in botones[0]._event_listeners.values() if escucha.type == "click")
        accion(None)
        assert guardados == [[[entrada.value or "0" for entrada in fila] for fila in vista.entradas_coeficientes]]
        assert len(navegados) == 1
        vista.entradas_vector_original[0].set_value("7")
        accion(None)
        assert len(guardados) == len(navegados) == 1
        assert all(boton.is_deleted for boton in botones)
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
