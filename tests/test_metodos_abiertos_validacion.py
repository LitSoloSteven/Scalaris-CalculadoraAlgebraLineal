"""Contrato y validación de entrada de los métodos abiertos."""
from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from src.backend.resolutores.raices.metodos_abiertos.contrato_abiertos import (
    EntradaMetodoAbierto,
)
from src.backend.resolutores.raices.metodos_abiertos.validacion_abiertos import (
    validar_entrada_abierta,
)


def _datos(**cambios):
    datos = {
        "metodo": "newton",
        "expresion": "x^3 - x - 2",
        "x0": 1.5,
        "tolerancia": 1e-6,
        "limite_iteraciones": 100,
    }
    datos.update(cambios)
    return datos


def test_entrada_usa_defaults_del_contrato():
    """Tolerancia y límite tienen los valores por defecto documentados."""
    entrada = EntradaMetodoAbierto(metodo="newton", expresion="x - 1", x0=0.0)
    assert entrada.tolerancia == 1e-6
    assert entrada.limite_iteraciones == 100
    assert entrada.x1 is None


def test_validacion_aplica_defaults_si_faltan_los_campos():
    """La captura mínima de Newton no necesita tolerancia ni límite."""
    entrada = validar_entrada_abierta({"metodo": "newton", "expresion": "x - 1", "x0": 0})
    assert entrada.tolerancia == 1e-6
    assert entrada.limite_iteraciones == 100
    assert entrada.x1 is None


def test_validacion_acepta_mapping_no_dict():
    """Cualquier Mapping es válido como entrada cruda."""
    entrada = validar_entrada_abierta(MappingProxyType(_datos()))
    assert entrada.expresion == "x^3 - x - 2"


def test_validacion_normaliza_espacios_de_la_expresion():
    """La expresión se recorta sin alterar su contenido matemático."""
    entrada = validar_entrada_abierta(_datos(expresion="  x - 1  "))
    assert entrada.expresion == "x - 1"


def test_newton_ignora_el_segundo_punto():
    """x1 solo pertenece al contrato de la secante."""
    entrada = validar_entrada_abierta(_datos(x1=99.0))
    assert entrada.x1 is None


def test_secante_exige_y_conserva_el_segundo_punto():
    """La secante necesita x1 finito y distinto de x0."""
    entrada = validar_entrada_abierta(_datos(metodo="secante", x0=1.0, x1=2.0))
    assert entrada.x1 == 2.0


@pytest.mark.parametrize("metodo", [None, "", "biseccion", "Newton", 1])
def test_metodo_desconocido_es_invalido(metodo):
    """Solo se admiten los literales newton y secante."""
    with pytest.raises(ValueError, match="método"):
        validar_entrada_abierta(_datos(metodo=metodo))


@pytest.mark.parametrize(
    "cambios",
    [
        {"expresion": ""},
        {"expresion": "   "},
        {"expresion": "x" * 513},
        {"expresion": None},
    ],
)
def test_expresion_invalida(cambios):
    """La expresión es obligatoria y respeta el máximo de la gramática."""
    with pytest.raises(ValueError, match="expresión"):
        validar_entrada_abierta(_datos(**cambios))


@pytest.mark.parametrize(
    "valor",
    [None, "", "1.5", True, float("nan"), float("inf"), 10**400],
)
def test_x0_invalido(valor):
    """x0 debe ser un número real finito."""
    with pytest.raises(ValueError, match="x0"):
        validar_entrada_abierta(_datos(x0=valor))


@pytest.mark.parametrize(
    "valor",
    [None, "", "2", True, float("nan"), float("inf")],
)
def test_secante_con_x1_invalido(valor):
    """x1 debe existir y ser un número real finito."""
    with pytest.raises(ValueError, match="x1"):
        validar_entrada_abierta(_datos(metodo="secante", x1=valor))


def test_secante_exige_puntos_distintos():
    """x0 == x1 anula el denominador de la secante."""
    with pytest.raises(ValueError, match="distintos"):
        validar_entrada_abierta(_datos(metodo="secante", x0=2.0, x1=2.0))


@pytest.mark.parametrize(
    "valor",
    [None, "", "1e-6", True, 0, -1e-6, float("nan"), float("inf"), 1e-16, 1.01],
)
def test_tolerancia_invalida(valor):
    """La tolerancia es numérica, finita y está dentro del rango documentado."""
    with pytest.raises(ValueError, match="tolerancia"):
        validar_entrada_abierta(_datos(tolerancia=valor))


@pytest.mark.parametrize("valor", [1e-15, 1e-6, 1.0])
def test_tolerancia_en_los_limites_es_valida(valor):
    """Los extremos inclusivos del rango se aceptan."""
    assert validar_entrada_abierta(_datos(tolerancia=valor)).tolerancia == valor


@pytest.mark.parametrize("valor", [0, 501, 3.0, True, "100", -1])
def test_limite_de_iteraciones_invalido(valor):
    """El límite es un entero entre 1 y 500."""
    with pytest.raises(ValueError, match="límite"):
        validar_entrada_abierta(_datos(limite_iteraciones=valor))


def test_entrada_devuelta_es_inmutable():
    """El contrato validado no puede modificarse después."""
    entrada = validar_entrada_abierta(_datos())
    with pytest.raises(FrozenInstanceError):
        entrada.tolerancia = 0.1


def test_entrada_que_no_es_mapping_es_invalida():
    """La validación rechaza listas y otros tipos no mapeables."""
    with pytest.raises(ValueError, match="diccionario"):
        validar_entrada_abierta([("metodo", "newton")])
