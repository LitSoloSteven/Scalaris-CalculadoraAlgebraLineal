"""Vigencia de preferencias modificadas mientras el trabajador real está pendiente."""
import asyncio

import pytest
from nicegui import run

from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


@pytest.mark.parametrize("atributo,valor", [
    ("tolerancia", "1e-9"), ("limite", "1"), ("unidad_angular", "grados"),
])
def test_preferencia_editada_durante_calculo_se_aplica_solo_al_recalcular(monkeypatch, atributo, valor):
    """Revoca el resultado anterior y admite un nuevo envío con la preferencia vigente."""
    async def comprobar(vista):
        """Retarda el transporte, conserva el motor y comprueba descarte y recuperación."""
        iniciado, liberar = asyncio.Event(), asyncio.Event()

        async def trabajar(calcular, captura):
            """Ejecuta el cálculo recibido una vez autorizada la entrega por el escenario."""
            iniciado.set()
            await liberar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", trabajar)
        vista.cargar_captura(captura_regla_falsa())
        tarea = asyncio.create_task(vista.resolver())
        await asyncio.wait_for(iniciado.wait(), 2)
        getattr(vista, atributo).set_value(valor)
        liberar.set()
        await asyncio.wait_for(tarea, 2)
        assert vista.ultimo_resultado is None and not vista.historial
        assert vista.obtener_contexto_ia().foco is None and vista.boton_resolver.enabled
        assert not list(vista.contenedor_detalle)
        await vista.resolver()
        entrada = vista.ultimo_resultado["entrada"]
        campo = {"tolerancia": "tolerancia", "limite": "limite_iteraciones",
                 "unidad_angular": "unidad_angular"}[atributo]
        assert str(entrada[campo]) == str(float(valor) if atributo == "tolerancia" else valor)
        assert len(vista.historial) == 1 and not vista.ocupado
    ejecutar_escenario(monkeypatch, comprobar)
