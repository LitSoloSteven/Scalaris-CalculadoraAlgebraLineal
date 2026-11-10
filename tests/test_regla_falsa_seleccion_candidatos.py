"""Selección explícita, transaccional y revocable de candidatos reales."""
from copy import deepcopy

import pytest

from tests.comun_regla_falsa_vista import ejecutar_escenario
from tests.test_regla_falsa_exploracion import preparar_busqueda


@pytest.mark.parametrize("cambio", ["funcion", "unidad", "rango", "paso", "limpiar", "cerrar", "modo"])
def test_accion_antigua_no_puede_cargar_intervalo(monkeypatch, cambio):
    """Los callbacks retenidos pierden autorización después de cambiar su contexto."""
    async def comprobar(vista):
        """Retiene objetos de respuesta y candidato, invalida y reproduce la acción vieja."""
        panel = preparar_busqueda(vista)
        await panel.explorar()
        respuesta = panel.respuesta
        candidato = next(actual for actual in respuesta["candidatos"] if actual["tipo"] == "cruce")
        _cambiar(vista, cambio)
        antes = vista.capturar()
        panel.seleccionar(respuesta, candidato)
        assert vista.capturar() == antes and vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


def _cambiar(vista, cambio):
    if cambio == "funcion":
        vista.expresion.set_value("x^2-3")
        vista.expresion.set_value("x^2-2")
    elif cambio == "unidad":
        vista.unidad_angular.set_value("grados")
    elif cambio == "rango":
        vista.exploracion.minimo.set_value("-3")
    elif cambio == "paso":
        vista.exploracion.paso.set_value(".2")
    elif cambio == "limpiar":
        vista.limpiar_todo()
    elif cambio == "cerrar":
        vista.cerrar()
        vista.reabrir()
    else:
        vista.modos.set_value("intervalo")


def test_candidato_copiado_y_registros_no_aptos_no_se_cargan(monkeypatch):
    """La pertenencia por identidad rechaza candidatos fabricados o copiados."""
    async def comprobar(vista):
        """Prueba un cruce copiado y la restricción real de un polo."""
        panel = preparar_busqueda(vista)
        await panel.explorar()
        respuesta = panel.respuesta
        antes = vista.capturar()
        panel.seleccionar(respuesta, deepcopy(respuesta["candidatos"][0]))
        assert vista.capturar() == antes
        vista.expresion.set_value("1/x")
        await panel.explorar()
        respuesta = panel.respuesta
        for candidato in respuesta["candidatos"]:
            panel.seleccionar(respuesta, candidato)
        assert vista.inferior.value == vista.superior.value == ""
    ejecutar_escenario(monkeypatch, comprobar)


def test_carga_es_transaccional_y_no_promete_cero_preferido(monkeypatch):
    """El cero evaluado carga su intervalo sin añadir un contrato inexistente al cálculo."""
    async def comprobar(vista):
        """Observa las dos ediciones y conserva preferencias inválidas sin validarlas."""
        panel = preparar_busqueda(vista, "x")
        panel.paso.set_value(".5")
        await panel.explorar()
        respuesta = panel.respuesta
        candidato = next(actual for actual in respuesta["candidatos"] if actual["tipo"] == "cero_evaluado")
        observaciones = []
        vista.inferior.on_value_change(lambda: observaciones.append(vista._cargando_captura))
        vista.superior.on_value_change(lambda: observaciones.append(vista._cargando_captura))
        vista.tolerancia.set_value("invalida")
        assert panel.respuesta is respuesta
        panel.seleccionar(respuesta, candidato)
        assert observaciones == [True, True]
        assert "cero_preferido" not in vista.capturar()
        assert vista.tolerancia.value == "invalida" and not vista.historial
        assert vista.modos.value == "intervalo" and panel.respuesta is None
    ejecutar_escenario(monkeypatch, comprobar)
