"""Regresiones de normalización, etiquetas y revocación de una ejecución configurada."""
import asyncio

import pytest
from nicegui import run

from src.frontend.controladores.regla_falsa.contexto_regla_falsa import resumir_contexto_regla_falsa
from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion
from src.frontend.controladores.regla_falsa.salidas_regla_falsa import datos_copia_configurada
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_normalizar_extremos_conserva_cero_y_reciente(monkeypatch):
    async def comprobar(vista):
        vista.cargar_captura(captura_regla_falsa(expresion="x*(x-1)", extremo_izquierdo="1",
                                               extremo_derecho="0", cero_preferido=1))
        await vista.resolver()
        assert vista.ultimo_resultado["aproximacion"] == 1
        assert vista.capturar()["cero_preferido"] == 1
        registro = vista.historial[0]["captura"]
        assert registro["cero_preferido"] == 1
        vista.cargar_captura(registro)
        await vista.resolver()
        assert vista.ultimo_resultado["aproximacion"] == 1
    ejecutar_escenario(monkeypatch, comprobar)


def test_conteo_sin_aproximacion_no_anuncia_valor_provisional():
    datos = calcular_presentacion(captura_regla_falsa(expresion="x+", criterio={"tipo": "iteraciones", "parametro": 1}))
    assert datos["resultado"]["estado"] == "ERROR"
    copia = next(iter(datos_copia_configurada(datos["resultado"], datos["ampliado"], 4).values()))
    assert "Aproximación no disponible" in copia
    contexto = resumir_contexto_regla_falsa(datos["resultado"], datos["ampliado"])
    assert contexto["etiqueta_aproximacion"] == "Aproximación no disponible"


@pytest.mark.parametrize("cambio", ["criterio", "parametro", "ida_y_vuelta", "cerrar"])
def test_configuracion_editada_no_publica_ejecucion_pendiente(monkeypatch, cambio):
    async def comprobar(vista):
        inicio, liberar = asyncio.Event(), asyncio.Event()

        async def trabajar(calcular, captura):
            inicio.set()
            await liberar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", trabajar)
        vista.cargar_captura(captura_regla_falsa(criterio={"tipo": "iteraciones", "parametro": 1}))
        tarea = asyncio.create_task(vista.resolver())
        await asyncio.wait_for(inicio.wait(), 2)
        if cambio == "criterio":
            vista.criterio.set_value("ancho")
        elif cambio == "cerrar":
            vista.cerrar()
            vista.reabrir()
        else:
            vista.parametros_criterio["iteraciones"].set_value("2")
            if cambio == "ida_y_vuelta":
                vista.parametros_criterio["iteraciones"].set_value(1)
        liberar.set()
        await asyncio.wait_for(tarea, 2)
        assert vista.ultimo_resultado is vista.ultimo_ampliado is None
        assert not vista.historial and not vista.ocupado
    ejecutar_escenario(monkeypatch, comprobar)
