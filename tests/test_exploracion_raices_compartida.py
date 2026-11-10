"""Compatibilidad de exploración compartida y selección inyectada."""
import json

import pytest

from src.frontend.controladores import exploracion_raices as comun
from src.frontend.controladores.biseccion import exploracion as anterior
from src.frontend.controladores.rango_exploracion_raices import rango_grafica
from tests.comun_biseccion_criterios import ejecutar_escenario
from tests.comun_exploracion_biseccion import preparar_exploracion, acciones_exploracion, activar_accion


@pytest.mark.parametrize("expresion", ["x^2-2", "x^2+1", "x", "1/(x-0.1234)", "sqrt(x)-1"])
def test_fachada_conserva_resultados_serializables(expresion):
    """Las fachadas usan el mismo servicio sin exigir extremos ni criterio válido."""
    captura = {"expresion": expresion, "x_min": "-2", "x_max": "2", "paso": ".1"}
    resultado = comun.resolver_exploracion(captura)
    assert anterior.resolver_exploracion is comun.resolver_exploracion
    assert resultado == anterior.resolver_exploracion(captura)
    assert resultado["estado"] == "EXITO"
    json.dumps(resultado, allow_nan=False)


@pytest.mark.parametrize("captura", [None, {}, {"x_min": "9" * 65},
    {"expresion": "x", "x_min": "-2", "x_max": "2", "paso": "nan"}])
def test_captura_invalida_conserva_error_granular(captura):
    """La entrada adversa devuelve error serializable sin publicar candidatos."""
    respuesta = comun.resolver_exploracion(captura)
    assert respuesta["estado"] == "ERROR"
    assert respuesta["candidatos"] == ()
    assert respuesta["mensaje"]
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("minimo,maximo", [("nan", "2"), ("1", "inf"), ("2", "1"), (True, "2")])
def test_rango_rechaza_extremos_no_utilizables(minimo, maximo):
    """La conversión no admite booleanos, infinitos ni rangos invertidos."""
    with pytest.raises(ValueError):
        rango_grafica({"x_min": minimo, "x_max": maximo})


def test_paso_automatico_no_desborda():
    """La división previa evita restar directamente los extremos gigantes."""
    assert comun.sugerir_paso({"x_min": "-1e308", "x_max": "1e308"}) == 1e306


def test_componente_conserva_la_seleccion_vigente(monkeypatch):
    """Un botón real carga el intervalo y una acción obsoleta no altera la vista."""
    async def comprobar(vista):
        panel = preparar_exploracion(vista, "x^2-2")
        await panel.explorar()
        boton = acciones_exploracion(panel)[0]
        accion_antigua = next(evento.handler for evento in boton._event_listeners.values() if evento.type == "click")
        activar_accion(boton)
        assert float(vista.inferior.value) < float(vista.superior.value)
        assert vista.ultimo_resultado is None
        vista.expresion.set_value("x^2+1")
        captura = vista.capturar()
        accion_antigua(None)
        assert vista.capturar() == captura
    ejecutar_escenario(monkeypatch, comprobar)
