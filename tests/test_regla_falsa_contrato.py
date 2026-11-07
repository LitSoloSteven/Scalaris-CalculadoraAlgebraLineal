"""Contrato de entrada y salida de regla falsa: campos, defaults y validacion."""
import math

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import (
    EntradaReglaFalsa,
    IteracionReglaFalsa,
    ResultadoReglaFalsa,
)
from src.backend.resolutores.raices.limites_raices import (
    LIMITE_ITERACIONES_DEFECTO,
    LIMITE_ITERACIONES_MAXIMO,
)
from src.backend.resolutores.raices.validacion_regla_falsa import (
    validar_entrada_regla_falsa,
)


def _datos(expresion="x**2-2", a=1, b=2, tol=1e-6, limite=100):
    return {
        "expresion": expresion,
        "extremo_izquierdo": a,
        "extremo_derecho": b,
        "tolerancia": tol,
        "limite_iteraciones": limite,
    }


def test_entrada_regla_falsa_admite_valores_validos():
    """Campos canonicos con tipos correctos."""
    entrada = EntradaReglaFalsa(
        expresion="x-1",
        extremo_izquierdo=0.0,
        extremo_derecho=2.0,
        tolerancia=1e-4,
    )
    assert entrada.tolerancia == 1e-4
    assert entrada.limite_iteraciones == LIMITE_ITERACIONES_DEFECTO
    assert entrada.intervalo_invertido is False
    assert entrada.unidad_angular == "radianes"
    assert entrada.advertencias == ()


def test_entrada_regla_falsa_defaults():
    """Tolerancia y limite tienen defaults."""
    entrada = EntradaReglaFalsa(
        expresion="x-1",
        extremo_izquierdo=0.0,
        extremo_derecho=2.0,
    )
    assert entrada.tolerancia == 1e-6
    assert entrada.limite_iteraciones == LIMITE_ITERACIONES_DEFECTO


def test_entrada_regla_falsa_aviso_de_intervalo_invertido():
    """Solo aparece el aviso si la entrada lo declara."""
    entrada = EntradaReglaFalsa(
        expresion="x-1",
        extremo_izquierdo=0.0,
        extremo_derecho=2.0,
        tolerancia=1e-4,
        intervalo_invertido=True,
    )
    assert len(entrada.advertencias) == 1


def test_iteracion_regla_falsa_defaults():
    """Los campos opcionales se mantienen en None o vacio."""
    fila = IteracionReglaFalsa(
        i=1,
        extremo_izquierdo=0.0,
        extremo_derecho=1.0,
        valor_izquierdo=-1.0,
        valor_derecho=1.0,
        aproximacion=0.5,
        valor_aproximacion=0.0,
        residuo=0.0,
        ancho=1.0,
        peso_secante=0.5,
        error_relativo_porcentual=None,
        signo_producto=-1,
        accion="reemplazar_b",
        intervalo_siguiente=(0.0, 0.5),
    )
    assert fila.error_relativo_porcentual is None
    assert fila.motivo_parada == ""


def test_resultado_regla_falsa_defaults():
    """Resultado sin iteraciones y con estado minimo."""
    resultado = ResultadoReglaFalsa(
        entrada=None,
        estado="EXITO",
        mensaje="ok",
        codigo_diagnostico="RAIZ_EN_EXTREMO",
        motivo_parada="raiz_en_extremo",
        aproximacion=1.0,
        residuo=0.0,
        intervalo_final=(1.0, 1.0),
        iteraciones=(),
        iteraciones_totales=0,
    )
    assert resultado.metodo == "regla_falsa"
    assert resultado.iteraciones == ()
    assert resultado.advertencias == ()


def test_validar_entrada_regla_falsa_acepta_captura_canonica():
    """La captura valida produce la entrada esperada."""
    entrada = validar_entrada_regla_falsa(_datos())
    assert entrada.expresion == "x**2-2"
    assert entrada.extremo_izquierdo == 1.0
    assert entrada.extremo_derecho == 2.0
    assert entrada.tolerancia == 1e-6
    assert entrada.limite_iteraciones == 100


def test_validar_entrada_regla_falsa_normaliza_intervalo_invertido():
    """Los extremos se ordenan y se marca la inversion."""
    entrada = validar_entrada_regla_falsa(_datos(a=2, b=1))
    assert entrada.extremo_izquierdo == 1.0
    assert entrada.extremo_derecho == 2.0
    assert entrada.intervalo_invertido is True


def test_validar_entrada_regla_falsa_rechaza_extremos_iguales():
    """a == b no forma intervalo."""
    with pytest.raises(ValueError, match="intervalo es invalido"):
        validar_entrada_regla_falsa(_datos(a=1, b=1))


@pytest.mark.parametrize("tol", [None, 0, -1, "1e-6", True, math.nan, math.inf])
def test_validar_entrada_regla_falsa_rechaza_tolerancia_invalida(tol):
    """La tolerancia debe ser positiva, finita y numerica no booleana."""
    with pytest.raises(ValueError, match="tolerancia"):
        validar_entrada_regla_falsa(_datos(tol=tol))


def test_validar_entrada_regla_falsa_exige_limite_no_nulo():
    """A diferencia de biseccion, regla falsa no admite None como ausencia."""
    with pytest.raises(ValueError, match="limite"):
        validar_entrada_regla_falsa(_datos(limite=None))


@pytest.mark.parametrize("limite", [0, -1, LIMITE_ITERACIONES_MAXIMO + 1, 1.5, True])
def test_validar_entrada_regla_falsa_rechaza_limite_invalido(limite):
    """Solo enteros del rango admitido son validos."""
    with pytest.raises(ValueError, match="límite"):
        validar_entrada_regla_falsa(_datos(limite=limite))


def test_validar_entrada_regla_falsa_acepta_limite_en_borde():
    """1 y el maximo son aceptados."""
    assert validar_entrada_regla_falsa(_datos(limite=1)).limite_iteraciones == 1
    entrada = validar_entrada_regla_falsa(_datos(limite=LIMITE_ITERACIONES_MAXIMO))
    assert entrada.limite_iteraciones == LIMITE_ITERACIONES_MAXIMO


@pytest.mark.parametrize("expresion", [None, "", "   "])
def test_validar_entrada_regla_falsa_rechaza_expresion_vacia(expresion):
    """La expresion es obligatoria."""
    with pytest.raises(ValueError, match="expresi"):
        validar_entrada_regla_falsa(_datos(expresion=expresion))


def test_validar_entrada_regla_falsa_rechaza_unidad_invalida():
    """La unidad angular solo admite radianes o grados."""
    datos = _datos()
    datos["unidad_angular"] = "vueltas"
    with pytest.raises(ValueError, match="unidad angular"):
        validar_entrada_regla_falsa(datos)