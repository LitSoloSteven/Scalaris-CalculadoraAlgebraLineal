"""Captura de regla falsa mediante conversiones compartidas y dominio real."""
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.validacion_regla_falsa import validar_entrada_regla_falsa
from src.frontend.controladores.regla_falsa.captura import preparar_entrada


def _captura():
    return {"expresion": "x^2-2", "extremo_izquierdo": "1", "extremo_derecho": "2"}


def test_captura_conserva_predeterminados_del_dominio():
    """Convierte extremos textuales sin duplicar los valores opcionales del contrato."""
    entrada = preparar_entrada(_captura())
    esperada = validar_entrada_regla_falsa({
        "expresion": "x^2-2", "extremo_izquierdo": 1.0, "extremo_derecho": 2.0,
    })
    assert entrada == esperada


def test_captura_normaliza_y_revalida_sin_perder_el_aviso():
    """La entrada canónica conserva la marca al convertirla otra vez desde su diccionario."""
    captura = _captura() | {"extremo_izquierdo": "2", "extremo_derecho": "1",
                            "tolerancia": "1e-9", "limite_iteraciones": "500.0",
                            "unidad_angular": "grados"}
    entrada = preparar_entrada(captura)
    assert entrada.extremo_izquierdo == 1 and entrada.extremo_derecho == 2
    assert entrada.tolerancia == 1e-9 and entrada.limite_iteraciones == 500
    assert entrada.unidad_angular == "grados" and entrada.intervalo_invertido
    assert entrada.advertencias and preparar_entrada(asdict(entrada)) == entrada
    assert captura["extremo_izquierdo"] == "2"


@pytest.mark.parametrize("campo,valor", [
    ("extremo_izquierdo", True), ("extremo_derecho", None),
    ("extremo_izquierdo", "1,5"), ("extremo_derecho", "inf"),
    ("extremo_izquierdo", "nan"), ("extremo_derecho", "1e999"),
    ("extremo_derecho", "1"), ("tolerancia", "0"),
    ("tolerancia", "-1"), ("tolerancia", "1e-999"),
    ("tolerancia", "nan"), ("tolerancia", True), ("tolerancia", None),
    ("limite_iteraciones", "1.0000000000000000001"),
    ("limite_iteraciones", "501"), ("limite_iteraciones", "0"),
    ("limite_iteraciones", True), ("limite_iteraciones", None),
    ("unidad_angular", "otra"), ("unidad_angular", None),
    ("intervalo_invertido", "sí"), ("expresion", ""), ("expresion", "x" * 513),
])
def test_captura_rechaza_campos_invalidos(campo, valor):
    """Rechaza conversión inválida y deja al dominio decidir límites y finitud."""
    with pytest.raises(ValueError):
        preparar_entrada(_captura() | {campo: valor})


@pytest.mark.parametrize("captura", [None, [], "x", {}, {"expresion": "x"}])
def test_captura_incompleta_produce_error_orientativo(captura):
    """Los campos ausentes y sobres incompatibles fallan antes de ejecutar el motor."""
    with pytest.raises(ValueError, match="Introduce|extremo"):
        preparar_entrada(captura)
