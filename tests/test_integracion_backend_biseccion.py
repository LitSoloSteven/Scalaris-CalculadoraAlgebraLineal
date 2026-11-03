"""Consumo del contrato numérico robusto en tablas, pasos y mensajes de la interfaz."""
from src.backend.resolutores.raices.contrato_biseccion import LIMITE_ITERACIONES_MAXIMO
from src.frontend.controladores.biseccion.controlador import resolver_captura, LIMITE_ITERACIONES_INTERFAZ
from src.frontend.controladores.biseccion.presentacion import filas_tabla, valor_columna, motivo


def _captura(expresion="x^2-2", intervalo=(1, 2), decimales=4):
    return dict(expresion=expresion, extremo_izquierdo=intervalo[0], extremo_derecho=intervalo[1],
                decimales=decimales, limite_iteraciones=100)


def test_porcentaje_interno_se_inspecciona_en_tabla_y_pasos():
    """La inspección usa el campo numérico del motor en vez del porcentaje ya redondeado."""
    respuesta = resolver_captura(_captura())
    fila = respuesta["iteraciones"][-1]
    assert filas_tabla(respuesta)[-1]["error_relativo"] == "0.00%"
    texto = filas_tabla(respuesta, True)[-1]["error_relativo"]
    assert float(texto.removesuffix("%")) == fila["error_relativo_valor"]
    assert texto == valor_columna(fila, "error_relativo", True)


def test_mensaje_y_diagnostico_de_estancamiento_llegan_a_la_vista():
    """Los cierres por capacidad mantienen la aproximación provisional y un motivo legible."""
    respuesta = resolver_captura(_captura("sin(x)", (1e16, 1e16 + 4), 15))
    assert respuesta["codigo_diagnostico"] == "ESTANCAMIENTO"
    assert respuesta["estado"] == "PRECISION_NO_ALCANZADA"
    assert "representación numérica" in motivo(respuesta)


def test_diagnostico_de_subdesbordamiento_no_es_raiz():
    """El adaptador conserva el error de capacidad, sin inventar una raíz en un extremo."""
    respuesta = resolver_captura(_captura("exp(-1000)", (0, 1)))
    assert respuesta["estado"] == "ERROR"
    assert respuesta["codigo_diagnostico"] == "SUBDESBORDAMIENTO"
    assert respuesta["aproximacion"] is None


def test_cero_evaluado_y_limite_compartido():
    """El aviso procede del dominio y la interfaz utiliza el límite canónico."""
    respuesta = resolver_captura(_captura("x", (0, 2)))
    assert respuesta["codigo_diagnostico"] == "CERO_EVALUADO"
    assert respuesta["aviso"] == respuesta["mensaje"]
    assert LIMITE_ITERACIONES_INTERFAZ == LIMITE_ITERACIONES_MAXIMO
