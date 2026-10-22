"""Regresiones del montaje y del contrato real entre captura y cálculo vectorial."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend.controladores.operaciones_vectores.captura import resolver_captura
from tests.comun_vista_vectorial import vista_vectorial_montada


def test_vista_vectorial_monta_tres_paneles_con_minimos(vista_vectorial_montada):
    """Las tres pestañas empiezan con suficientes vectores para calcular."""
    vista = vista_vectorial_montada
    assert [len(panel.vectores) for panel in vista.paneles.values()] == [2, 1, 2, 1]
    assert list(vista.panel_combinacion.vectores) == ["b", "v_1"]


@pytest.mark.parametrize("operacion,opciones,datos,esperado", [
    ("suma_resta", {"operacion": "suma", "estricto": False}, [["1/3", "2", "-3"], ["2/3", "-2", "4"]], ["1", "0", "1"]),
    ("suma_resta", {"operacion": "resta", "estricto": False}, [["1/3", "2", "-3"], ["2/3", "-2", "4"]], ["-1/3", "4", "-7"]),
    ("escalar", {"escalar": "-3"}, [["1/3", "2", "-3"]], ["-1", "-6", "9"]),
])
def test_calculo_vectorial_recibe_el_contrato_del_controlador(vista_vectorial_montada, operacion, opciones, datos, esperado):
    """El controlador real calcula fracciones y signos a partir de la captura."""
    vista = vista_vectorial_montada
    vista.al_cambiar_pestana(SimpleNamespace(value=operacion))
    for vector, celdas in zip(vista.panel_vectorial.vectores.values(), datos):
        vector["celdas"] = dict(enumerate(celdas))
    resultado = json.loads(resolver_captura(operacion, opciones, vista._capturar()))
    assert resultado["estado"] != "ERROR"
    assert resultado["matriz_resultado"]["datos"] == [[valor] for valor in esperado]


def test_combinacion_vectorial_no_retira_objetivo_de_la_captura(vista_vectorial_montada):
    """El objetivo permanece disponible tras construir la carga de combinación."""
    vista = vista_vectorial_montada
    vista.al_cambiar_pestana(SimpleNamespace(value="combinacion_lineal"))
    vista.panel_combinacion.vectores["b"]["celdas"] = {0: "2", 1: "4", 2: "6"}
    vista.panel_combinacion.vectores["v_1"]["celdas"] = {0: "1", 1: "2", 2: "3"}
    captura = vista._capturar()
    resultado = json.loads(resolver_captura(vista.operacion_activa, vista._opciones_calculo(), captura))
    assert resultado["estado"] == "UNICA"
    assert resultado["coeficientes_texto"] == ["2"]
    assert "b" in captura


def test_entrada_invalida_se_conserva_y_el_dominio_la_rechaza(vista_vectorial_montada):
    """Una celda inválida no se reemplaza silenciosamente por cero."""
    vista = vista_vectorial_montada
    vista.panel_suma_resta.vectores["u"]["celdas"][1] = "abc"
    captura = vista._capturar()
    resultado = json.loads(resolver_captura(vista.operacion_activa, vista._opciones_calculo(), captura))
    assert captura["u"]["datos"][1] == "abc"
    assert resultado["estado"] == "ERROR"
    assert "abc" in resultado["mensaje"]
    assert vista.obtener_senales_ia().invalida.foco == (0, 1)


def test_limpiar_solo_vacia_operacion_activa_y_detiene_reproduccion(vista_vectorial_montada):
    """La limpieza conserva las otras pestañas, dimensión y orientación."""
    vista = vista_vectorial_montada
    vista.panel_suma_resta.vectores["u"].update(orientacion="fila", celdas={0: "7"})
    vista.panel_escalar.vectores["u"]["celdas"][0] = "8"
    reproductor = Mock()
    vista.reproductor_pasos = reproductor
    vista.resultado_actual = {"estado": "EXITO"}
    vista._huella_resultado = "anterior"
    vista.limpiar()
    assert vista.panel_suma_resta.vectores["u"]["celdas"] == {}
    assert vista.panel_suma_resta.vectores["u"]["orientacion"] == "fila"
    assert vista.panel_suma_resta.dimension == 3
    assert vista.panel_escalar.vectores["u"]["celdas"] == {0: "8"}
    assert vista.resultado_actual is None
    assert vista._huella_resultado is None
    reproductor.detener.assert_called_once_with()


def test_pestana_nueva_retira_resultado_sin_perder_celdas(vista_vectorial_montada):
    """El evento real de las pestañas actualiza operación y estado vacío."""
    vista = vista_vectorial_montada
    vista.panel_suma_resta.vectores["u"]["celdas"][0] = "9"
    vista.resultado_actual = {"estado": "EXITO"}
    vista.pestanas.set_value("escalar")
    assert vista.operacion_activa == "escalar"
    assert vista.resultado_actual is None
    assert vista.panel_suma_resta.vectores["u"]["celdas"] == {0: "9"}


def test_fallo_imprevisto_restaura_boton_y_no_registra_datos(monkeypatch, caplog, vista_vectorial_montada):
    """Un fallo deja el cálculo disponible y registra solo un diagnóstico genérico."""
    from src.frontend.vistas.operaciones_vectores import vista_operaciones_vectores as modulo
    vista = vista_vectorial_montada
    monkeypatch.setattr(modulo, "resolver_captura", Mock(side_effect=RuntimeError("dato privado ficticio")))
    avisos = Mock()
    monkeypatch.setattr(ui, "notify", avisos)
    asyncio.run(vista.calcular())
    assert vista.boton_calcular.enabled
    assert "loading" not in vista.boton_calcular._props
    assert "dato privado ficticio" not in caplog.text
    avisos.assert_called_once()

