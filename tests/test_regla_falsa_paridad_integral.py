"""Recorrido de búsqueda, cálculo configurado y restauración del ejercicio."""
import math

import pytest
from nicegui import ui

from tests.comun_exploracion_biseccion import activar_accion
from tests.comun_regla_falsa_vista import ejecutar_escenario


@pytest.mark.parametrize("unidad,maximo,raiz", [("grados", "60", 30), ("radianes", "1", math.pi / 6)])
def test_busqueda_trigonometrica_conserva_unidad_hasta_restaurar_el_reciente(monkeypatch, unidad, maximo, raiz):
    """El intervalo hallado y la traza mantienen el significado angular de la captura."""
    async def comprobar(vista):
        """Recorre el flujo con un cruce real en la unidad parametrizada."""
        vista.expresion.set_value("2sin(x)-1")
        vista.unidad_angular.set_value(unidad)
        vista.criterio.set_value("ancho")
        vista.parametros_criterio["ancho"].set_value("1e-6")
        vista.modos.set_value("busqueda")
        panel = vista.exploracion
        panel.minimo.set_value("0")
        panel.maximo.set_value(maximo)
        assert vista.inferior.value == vista.superior.value == ""

        await vista.enviar_captura()
        respuesta = panel.respuesta
        candidato, = (c for c in respuesta["candidatos"] if c["tipo"] in {"cruce", "cero_evaluado"})
        panel.seleccionar(respuesta, candidato)
        await vista.enviar_captura()

        resultado = vista.ultimo_resultado
        assert resultado["metodo"] == "regla_falsa" and resultado["estado"] == "EXITO"
        assert resultado["aproximacion"] == pytest.approx(raiz, abs=1e-6)
        assert resultado["entrada"]["unidad_angular"] == unidad
        registro, = vista.historial
        vista.limpiar_todo()
        vista.unidad_angular.set_value("radianes" if unidad == "grados" else "grados")
        boton = next(e for e in vista.recientes.descendants() if isinstance(e, ui.button))
        activar_accion(boton)
        assert vista.capturar() == registro["captura"]
        assert vista.ultimo_resultado is None

    ejecutar_escenario(monkeypatch, comprobar)
