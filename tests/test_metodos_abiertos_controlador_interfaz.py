"""Contrato serializable del adaptador público de métodos abiertos."""
import json

from src.frontend.controladores.metodos_abiertos import resolver_captura


def test_resolver_captura_despacha_newton_y_secante():
    """El adaptador ejecuta ambos métodos y entrega resultados JSON seguros."""
    newton = resolver_captura({
        "metodo": "newton", "expresion": "x^3 - x - 2", "x0": "1.5",
        "tolerancia": "1e-6", "limite_iteraciones": "100",
    })
    secante = resolver_captura({
        "metodo": "secante", "expresion": "x^3 - x - 2", "x0": "1", "x1": "2",
        "tolerancia": "1e-6", "limite_iteraciones": "100",
    })

    assert newton["estado"] == "EXITO"
    assert newton["iteraciones_totales"] == 2
    assert abs(newton["raiz"] - 1.5213797068) < 1e-6
    assert secante["estado"] == "EXITO"
    assert secante["iteraciones_totales"] == 6
    json.dumps(newton, allow_nan=False)
    json.dumps(secante, allow_nan=False)


def test_capturas_invalidas_regresan_error_serializable():
    """Una conversión inválida devuelve un error de entrada sin lanzar excepción."""
    resultado = resolver_captura({"metodo": "newton", "expresion": "x^2", "x0": "no es número"})

    assert resultado["estado"] == "ERROR"
    assert resultado["codigo_diagnostico"] == "ENTRADA_INVALIDA"
    json.dumps(resultado, allow_nan=False)


def test_captura_numerica_con_longitud_excesiva_se_rechaza_antes_de_convertir():
    """El adaptador limita el tamaño de los textos numéricos que recibe."""
    resultado = resolver_captura({
        "metodo": "secante", "expresion": "x^2 - 2", "x0": "1", "x1": "2" * 65,
    })

    assert resultado["estado"] == "ERROR"
    assert resultado["codigo_diagnostico"] == "ENTRADA_INVALIDA"
    assert "64 caracteres" in resultado["mensaje"]
