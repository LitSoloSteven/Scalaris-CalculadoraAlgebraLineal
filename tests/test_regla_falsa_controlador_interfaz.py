"""Integración del adaptador con los estados y la traza del motor real."""
import importlib
import json
import math
from dataclasses import asdict, replace

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import ResultadoReglaFalsa
from src.backend.resolutores.raices.regla_falsa import regla_falsa
from src.frontend.controladores.regla_falsa.captura import preparar_entrada
from src.frontend.controladores.regla_falsa.controlador import resolver_captura
from src.frontend.controladores.regla_falsa.serializacion import serializar_resultado


def _captura():
    return {"expresion": "x^2-2", "extremo_izquierdo": "1", "extremo_derecho": "2"}


@pytest.mark.parametrize("cambios,estado,codigo,filas", [
    ({}, "EXITO", "TOLERANCIA_RESIDUO", 9),
    ({"expresion": "x-1"}, "EXITO", "RAIZ_EN_EXTREMO", 0),
    ({"expresion": "x", "extremo_izquierdo": "0"}, "EXITO", "RAIZ_EN_EXTREMO", 0),
    ({"expresion": "x-1.5"}, "EXITO", "RAIZ_EN_APROXIMACION", 1),
    ({"expresion": "x^2+1", "extremo_izquierdo": "-1", "extremo_derecho": "1"},
     "SIN_CAMBIO_DE_SIGNO", "SIN_CAMBIO_DE_SIGNO", 0),
    ({"expresion": "sqrt(x)", "extremo_izquierdo": "-1"}, "ERROR", "DOMINIO_INVALIDO", 0),
    ({"limite_iteraciones": "1"}, "LIMITE_ITERACIONES", "LIMITE_ITERACIONES", 1),
    ({"extremo_izquierdo": math.nextafter(math.sqrt(2), -math.inf),
      "extremo_derecho": math.sqrt(2), "tolerancia": "1e-30"},
     "ESTANCAMIENTO", "ESTANCAMIENTO_NUMERICO", 1),
    ({"expresion": "x+"}, "ERROR", "EXPRESION_INVALIDA", 0),
])
def test_controlador_conserva_el_sobre_real(cambios, estado, codigo, filas):
    """Compara todos los campos con el dominio sin reinterpretar estados ni calcular métricas."""
    captura = _captura() | cambios
    respuesta = resolver_captura(captura)
    assert respuesta == asdict(regla_falsa(preparar_entrada(captura)))
    assert (respuesta["estado"], respuesta["codigo_diagnostico"]) == (estado, codigo)
    assert respuesta["iteraciones_totales"] == len(respuesta["iteraciones"]) == filas
    json.dumps(respuesta, allow_nan=False)


def test_controlador_conserva_aviso_invertido_aun_con_error_sintactico():
    """La normalización de captura sigue visible cuando el motor no publica entrada."""
    respuesta = resolver_captura(_captura() | {
        "expresion": "x+", "extremo_izquierdo": "2", "extremo_derecho": "1",
    })
    assert respuesta["estado"] == "ERROR" and respuesta["entrada"] is None
    assert respuesta["advertencias"] == preparar_entrada(_captura() | {
        "extremo_izquierdo": "2", "extremo_derecho": "1",
    }).advertencias


@pytest.mark.parametrize("captura", [None, {}, {"expresion": "x", "extremo_izquierdo": True}])
def test_controlador_publica_errores_de_captura_completos(captura):
    """Los fallos previos al cálculo ofrecen el mismo sobre finito sin aproximación inventada."""
    respuesta = resolver_captura(captura)
    assert set(respuesta) == set(asdict(ResultadoReglaFalsa()))
    assert respuesta["estado"] == "ERROR" and respuesta["codigo_diagnostico"] == "ENTRADA_INVALIDA"
    assert respuesta["aproximacion"] is None and respuesta["iteraciones"] == ()
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("error", [ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError])
def test_controlador_no_expone_detalles_de_fallos_inesperados(monkeypatch, error):
    """Los fallos de adaptación previstos no filtran mensajes internos del motor."""
    modulo = importlib.import_module("src.frontend.controladores.regla_falsa.controlador")

    def fallar(_entrada):
        raise error("detalle privado del evaluador")

    monkeypatch.setattr(modulo, "regla_falsa", fallar)
    respuesta = modulo.resolver_captura(_captura())
    assert respuesta["codigo_diagnostico"] == "ERROR_ADAPTACION"
    assert "privado" not in respuesta["mensaje"]
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("campo,valor", [
    ("aproximacion", math.nan), ("residuo", math.inf),
    ("intervalo_final", (0, -math.inf)),
    ("contexto_fallo", {"etapa": "iteracion", "x_fallo": math.nan}),
    ("informe_continuidad", {"evidencia": ({"abscisa": math.inf},)}),
])
def test_serializacion_rechaza_no_finitos_anidados(campo, valor):
    """La salida verifica finitud en todo el sobre, incluidos diagnósticos y continuidad."""
    with pytest.raises(ValueError, match="representar"):
        serializar_resultado(replace(ResultadoReglaFalsa(), **{campo: valor}))


def test_serializacion_no_comparte_datos_mutables_del_resultado():
    """Editar una salida no altera la evidencia que conserva el motor."""
    resultado = regla_falsa(preparar_entrada(_captura()))
    respuesta = serializar_resultado(resultado)
    respuesta["informe_continuidad"]["mensaje"] = "otro"
    assert resultado.informe_continuidad["mensaje"] != "otro"
    with pytest.raises(ValueError, match="contrato"):
        serializar_resultado({})
