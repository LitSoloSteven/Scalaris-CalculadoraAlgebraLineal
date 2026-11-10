"""Eventos nativos adversos y alternativa completa por campos editables."""
from types import SimpleNamespace

import pytest

from src.frontend.controladores.seleccion_muestra_raices import abscisa_muestreada
from tests.comun_regla_falsa_vista import ejecutar_escenario


def evento_muestra(panel, indice):
    """Construye el sobre nativo de un único punto de la curva publicada."""
    muestra = panel.respuesta["muestra"]
    return {"points": [{"curveNumber": 0, "pointIndex": indice, "customdata": panel.identidad,
                        "x": muestra["x"][indice], "y": muestra["y"][indice]}]}


@pytest.mark.parametrize("cambio", [
    {}, {"points": []}, {"points": [None]}, {"points": [{}, {}]},
    {"curveNumber": 1}, {"curveNumber": False}, {"pointIndex": -1}, {"pointIndex": True},
    {"pointIndex": 999}, {"customdata": "antigua"}, {"x": float("nan")}, {"x": 3},
    {"y": None}, {"y": float("inf")}, {"x": True},
])
def test_eventos_manipulados_no_se_aceptan(cambio):
    """El controlador rechaza puntos ajenos, huecos, no finitos y sobres múltiples."""
    punto = {"curveNumber": 0, "pointIndex": 0, "customdata": "vigente", "x": 1, "y": 2}
    datos = cambio if not cambio or "points" in cambio else {"points": [{**punto, **cambio}]}
    assert abscisa_muestreada(datos, {"x": [1], "y": [2]}, "vigente") is None


def test_click_confirmar_cancelar_y_curva_obsoleta(monkeypatch):
    """Solo la confirmación escribe extremos; una curva sustituida no carga un borrador."""
    async def comprobar(vista):
        """Combina puntos, regeneración de curva y edición manual sobre controles reales."""
        panel, seleccion = vista.vista_previa, vista.seleccion_grafico
        vista.expresion.set_value("x^2-2")
        await panel.tarea
        anterior = evento_muestra(panel, 220)
        seleccion.iniciar()
        seleccion._marcar(SimpleNamespace(args=anterior))
        seleccion._marcar(SimpleNamespace(args=evento_muestra(panel, 240)))
        assert vista.inferior.value == vista.superior.value == ""
        seleccion.cancelar(devolver_foco=True)
        assert not seleccion.activa and vista.ultimo_resultado is None
        await panel.actualizar()
        seleccion.iniciar()
        seleccion._marcar(SimpleNamespace(args=anterior))
        assert seleccion.campos[0].value == ""
        seleccion.campos[0].set_value("1.1234567")
        seleccion.campos[1].set_value("2.1234567")
        seleccion.confirmar()
        assert vista.inferior.value == "1.1234567" and vista.superior.value == "2.1234567"
        assert vista.ultimo_resultado is None and not vista.historial and not seleccion.activa
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("valores", [("", "2"), ("2", "1"), ("1", "1"), ("nan", "2"), ("1", "inf")])
def test_confirmacion_invalida_conserva_captura(monkeypatch, valores):
    """La entrada manual inválida mantiene el borrador abierto con un mensaje útil."""
    async def comprobar(vista):
        """Confirma valores adversos sin necesitar muestras para la alternativa de teclado."""
        seleccion = vista.seleccion_grafico
        seleccion.iniciar()
        for campo, valor in zip(seleccion.campos, valores):
            campo.set_value(valor)
        seleccion.confirmar()
        assert seleccion.activa and seleccion.estado.text
        assert vista.inferior.value == vista.superior.value == "" and vista.ultimo_resultado is None
        vista.expresion.set_value("x")
        assert not seleccion.activa
    ejecutar_escenario(monkeypatch, comprobar)
