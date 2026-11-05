"""Consumo de criterios, cierres y JSON estricto a través del controlador existente."""
import json
from dataclasses import replace

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.frontend.controladores.biseccion import controlador
from src.frontend.controladores.biseccion.presentacion import construir_pasos, filas_tabla


def _captura(criterio=None):
    return dict(expresion="x^2-2", extremo_izquierdo="1", extremo_derecho="2",
                decimales=4, limite_iteraciones=100, criterio=criterio)


@pytest.mark.parametrize("tipo,parametro,filas", [
    ("relativo", 1, 7), ("ancho", .01, 8), ("decimales", 2, 8),
    ("residuo", .1, 4), ("iteraciones", 3, 3),
])
def test_controlador_no_exige_ancho_a_otro_criterio(tipo, parametro, filas):
    """El éxito relativo o residual no se descarta por la tolerancia decimal heredada."""
    respuesta = controlador.resolver_captura(_captura({"tipo": tipo, "parametro": parametro}))
    assert respuesta["estado"] == ("ITERACIONES_COMPLETADAS" if tipo == "iteraciones" else "EXITO")
    assert len(respuesta["iteraciones"]) == filas
    assert respuesta["criterio_solicitado"] == {"tipo": tipo, "parametro": parametro}
    assert respuesta["entrada"]["criterio"] == respuesta["criterio_solicitado"]
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("cambio", [
    {"estado": "ITERACIONES_COMPLETADAS"}, {"motivo_parada": "ancho_menor_que_E"},
    {"iteraciones": ()},
])
def test_controlador_rechaza_cierre_ordinario_incoherente(monkeypatch, cambio):
    """Una respuesta defectuosa del motor no se publica como criterio satisfecho."""
    captura = _captura({"tipo": "relativo", "parametro": 1})
    resultado = biseccion(controlador.preparar_entrada(captura))
    monkeypatch.setattr(controlador, "biseccion", lambda entrada: replace(resultado, **cambio))
    respuesta = controlador.resolver_captura(captura)
    assert respuesta["estado"] == "ERROR"
    json.dumps(respuesta, allow_nan=False)


def test_carga_antigua_conserva_tabla_y_procedimiento():
    """La captura previa sin criterio obtiene el mismo recorrido decimal y reproductor."""
    captura = _captura()
    del captura["criterio"]
    respuesta = controlador.calcular_presentacion(captura)
    pasos, grupos = construir_pasos(respuesta)
    assert respuesta["estado"] == "EXITO"
    assert respuesta["criterio_solicitado"] == {"tipo": "decimales", "parametro": 4}
    assert len(respuesta["iteraciones"]) == 15
    assert len(filas_tabla(respuesta)) == 15
    assert len(pasos) == 17
    assert grupos[-1].indices_pasos == (16,)
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("expresion,intervalo", [
    ("1/x", (-1, 1)), ("exp(-1000)", (0, 1)), ("x**2+1", (-1, 1)),
    ("sin(x)", (1e16, 1e16 + 4)), ("x", (0, 2)),
])
def test_salidas_excepcionales_y_diagnosticos_se_serializan(expresion, intervalo):
    """Los errores, la falta de signo, el estancamiento y el cero conservan solicitud y JSON finito."""
    captura = {**_captura({"tipo": "relativo", "parametro": 1}), "expresion": expresion,
               "extremo_izquierdo": intervalo[0], "extremo_derecho": intervalo[1]}
    respuesta = controlador.resolver_captura(captura)
    assert respuesta["criterio_solicitado"]["tipo"] == "relativo"
    assert respuesta["codigo_diagnostico"]
    json.dumps(respuesta, allow_nan=False)
