"""Fórmulas, pasos y figura obtenidos del resultado numérico real."""
import json

import pytest

from src.frontend.controladores.regla_falsa.controlador import resolver_captura
from src.frontend.controladores.regla_falsa.formulas_procedimiento import formulas_iteracion
from src.frontend.controladores.regla_falsa.pasos import construir_pasos, referencia_paso
from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion
from src.frontend.controladores.regla_falsa.tabla import filas_tabla
from src.frontend.vistas.regla_falsa.figura import crear_figura
from tests.comun_regla_falsa_vista import captura_regla_falsa


@pytest.mark.parametrize("cambios", [{}, {"limite_iteraciones": "1"}, {"expresion": "x+"},
                                    {"expresion": "x", "extremo_izquierdo": "0"},
                                    {"expresion": "x^2+1"}])
def test_pasos_conservan_traza_y_estado_incluso_sin_filas(cambios):
    """El cierre y los pasos describen datos reales sin atribuir éxito a un límite o error."""
    respuesta = resolver_captura(captura_regla_falsa(**cambios))
    pasos, grupos = construir_pasos(respuesta)
    assert len(pasos) == len(respuesta["iteraciones"]) + 2
    assert pasos[-1].explicacion == respuesta["mensaje"]
    assert grupos[-1].indices_pasos == (len(pasos) - 1,)
    for paso, fila in zip(pasos[1:-1], respuesta["iteraciones"]):
        assert paso.cuerpo is fila
        foco = referencia_paso(paso, len(pasos))
        assert foco.indice == paso.indice + 1 and foco.captura.detalle["iteracion"] is fila
    if respuesta["estado"] != "EXITO":
        assert "Convergió" not in pasos[-1].descripcion


def test_formulas_y_figura_conservan_valores_de_la_misma_fila():
    """La secante usa extremos del motor y distingue su cruce del valor evaluado."""
    datos = calcular_presentacion(captura_regla_falsa())
    respuesta, muestra = datos["resultado"], datos["muestra"]
    assert respuesta == resolver_captura(captura_regla_falsa())
    fila = respuesta["iteraciones"][0]
    formulas = formulas_iteracion(fila)
    assert r"\frac{f(a)(b-a)}{f(b)-f(a)}" in formulas[1]
    assert format(fila["aproximacion"], ".17g") in formulas[1]
    assert filas_tabla((fila,), True)[0]["aproximacion"] == format(fila["aproximacion"], ".17g")
    figura = crear_figura(respuesta, muestra, fila)
    assert list(figura.data[1].x) == [fila["extremo_izquierdo"], fila["extremo_derecho"]]
    assert list(figura.data[2].y) == [0]
    assert list(figura.data[3].y) == [fila["valor_aproximacion"]]
    assert list(figura.data[4].x) == list(fila["intervalo_siguiente"])
    json.loads(figura.to_json())


def test_error_no_muestrea_y_raiz_extrema_se_dibuja_sin_secante():
    """El gráfico no simula filas cuando el resultado no las contiene."""
    error = calcular_presentacion(captura_regla_falsa(expresion="x+"))
    assert error["muestra"] is None and error["aviso_grafica"]
    assert not crear_figura(error["resultado"], None).data
    cero = calcular_presentacion(captura_regla_falsa(expresion="x", extremo_izquierdo="0"))
    figura = crear_figura(cero["resultado"], cero["muestra"])
    assert len(figura.data) == 2 and list(figura.data[-1].x) == [0]
