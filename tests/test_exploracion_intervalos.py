"""Contratos de clasificación conservadora y aislamiento de evaluaciones inválidas."""
import json
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos


def _explorar(expresion, minimo=-2, maximo=2, paso=0.5):
    return explorar_intervalos(EntradaExploracion(expresion, minimo, maximo, paso))


@pytest.mark.parametrize("paso,tipo", [(0.5, "cero_evaluado"), (0.6, "cruce")])
def test_dos_candidatos_aunque_extremos_tengan_mismo_signo(paso, tipo):
    """Detecta ambos candidatos de x²-1 con ceros únicos o cruces según la malla."""
    resultado = _explorar("x**2-1", paso=paso)
    assert len(resultado.candidatos) == 2
    assert all(candidato.tipo == tipo for candidato in resultado.candidatos)
    for candidato, raiz in zip(resultado.candidatos, (-1, 1)):
        assert candidato.intervalo[0] <= raiz <= candidato.intervalo[1]
        assert candidato.intervalo[0] < candidato.intervalo[1]
    assert resultado.advertencias


@pytest.mark.parametrize("expresion,raiz", [("x+2", -2), ("x-2", 2), ("x", 0)])
def test_cero_unico_incluso_en_extremos(expresion, raiz):
    """Cada cero compartido aparece una vez con un vecino evaluable distinto."""
    candidatos = _explorar(expresion).candidatos
    assert len(candidatos) == 1
    assert candidatos[0].tipo == "cero_evaluado"
    assert candidatos[0].abscisa == raiz
    assert candidatos[0].valor == 0
    assert candidatos[0].intervalo[0] < candidatos[0].intervalo[1]


def test_hueco_no_se_une_como_cruce():
    """Una división inválida separa vecinos de signos contrarios."""
    resultado = _explorar("1/x", -1, 1, 1)
    assert [candidato.tipo for candidato in resultado.candidatos] == ["segmento_invalido"] * 2
    assert all(candidato.mensaje for candidato in resultado.candidatos)


def test_polo_estructural_entre_muestras_no_es_cruce():
    """Un polo afín no muestreado conserva su diagnóstico estructural."""
    candidatos = _explorar("1/(x-.1)", -1, 1, 2).candidatos
    assert len(candidatos) == 1
    assert candidatos[0].tipo == "discontinuidad"
    assert "denominador" in candidatos[0].mensaje


def test_cero_aislado_entre_fallos_no_inventa_intervalo_apto():
    """No propone seleccionar un cero cuyos vecinos son inválidos."""
    candidatos = _explorar("sqrt(-x*x)", -1, 1, 1).candidatos
    assert len(candidatos) == 2
    assert all(candidato.tipo == "segmento_invalido" for candidato in candidatos)


@pytest.mark.parametrize("expresion", ["(x-.1)**2", "1e-200*(x-.1)**2", "1e200*(x-.1)**2"])
def test_contacto_posible_por_evidencia_relativa(expresion):
    """El mínimo local tiene diagnóstico provisional independiente de su escala."""
    candidatos = _explorar(expresion, -1, 1, .5).candidatos
    assert len(candidatos) == 1
    assert candidatos[0].tipo == "posible_contacto"
    assert "no certifica" in candidatos[0].mensaje


@pytest.mark.parametrize("expresion", ["1e-200", "x*x+1", "1e200*(x*x+1)", "exp(x)"])
def test_valores_pequenos_o_grandes_no_bastan_para_candidato(expresion):
    """Sin contraste local ni cambio de signo no afirma contactos o polos."""
    assert _explorar(expresion).candidatos == ()


def test_signos_sin_producto_que_subdesborde():
    """Los cruces persisten cuando multiplicar los valores perdería el signo."""
    candidatos = _explorar("1e-200*(x-.1)", -1, 1, 2).candidatos
    assert len(candidatos) == 1
    assert candidatos[0].tipo == "cruce"


@pytest.mark.parametrize("expresion", ["sqrt(x)-1", "exp(x)", "1/x", "x*x-1"])
def test_resultado_serializable_sin_nan_ni_infinito(expresion):
    """El resultado completo incluso con fallos admite JSON estricto."""
    resultado = _explorar(expresion, -1000, 1000, 100)
    assert json.loads(json.dumps(asdict(resultado), allow_nan=False))["evaluaciones"] == 21


@pytest.mark.parametrize("expresion", ["__import__('os')", "x.real", "x[0]", "lambda: x", "y", "sin(x,x)"])
def test_sintaxis_no_segura_rechazada(expresion):
    """La exploración conserva el catálogo y los límites del evaluador seguro."""
    with pytest.raises(ValueError):
        _explorar(expresion)
