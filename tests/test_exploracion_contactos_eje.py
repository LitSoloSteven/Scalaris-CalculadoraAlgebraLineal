"""Evidencia local y búsqueda limitada de contactos sin certificación de raíces pares."""
import json
import math
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion, MuestraExploracion
from src.backend.resolutores.raices.evaluacion_exploracion import muestrear_punto
from src.backend.resolutores.raices.evaluador_funcion import compilar
from src.backend.resolutores.raices.refinamiento_contactos import refinar_contacto


def _refinar(expresion, presupuesto=24):
    entrada = EntradaExploracion(expresion, -.5, .5, .5)
    funcion = compilar(expresion)
    muestras = tuple(muestrear_punto(funcion, posicion) for posicion in (-.5, 0, .5))
    return refinar_contacto(entrada, funcion, muestras, presupuesto)[0]


@pytest.mark.parametrize("escala", ["1", "1e-200", "1e200", "-1"])
def test_mejora_local_independiente_de_escala(escala):
    """Reduce magnitud e intervalo manteniendo diagnóstico provisional y cifras sin redondear."""
    candidato = _refinar(f"{escala}*(x-.1)**2")
    evidencia = candidato.evidencia_contacto
    assert candidato.tipo == "posible_contacto" and candidato.valor != 0
    assert abs(candidato.abscisa - .1) < .0001
    assert abs(candidato.valor) < abs(evidencia.valor_inicial)
    assert candidato.intervalo[1] - candidato.intervalo[0] < .001
    assert evidencia.escala_inicial > abs(evidencia.valor_inicial)
    assert evidencia.evaluaciones == 24 and evidencia.refinamientos == 12
    assert evidencia.motivo == "limite_refinamientos" and "no certifica" in candidato.mensaje
    json.dumps(asdict(candidato), allow_nan=False)


def test_cero_descubierto_tiene_vecino_y_no_intervalo_degenerado():
    """Un cero realmente evaluado se reclasifica con intervalo apto y se detiene sin bisecar."""
    candidato = _refinar("(x-.125)**2")
    assert candidato.tipo == "cero_evaluado" and candidato.abscisa == .125 and candidato.valor == 0
    assert candidato.abscisa in candidato.intervalo and candidato.intervalo[0] < candidato.intervalo[1]
    assert candidato.evidencia_contacto.motivo == "cero_evaluado"
    assert candidato.evidencia_contacto.evaluaciones == 4


def test_minimo_positivo_pronunciado_no_se_afirma_como_raiz():
    """Un suelo pequeño no nulo sigue siendo solo un posible contacto con evidencia inspeccionable."""
    candidato = _refinar("(x-.1)**2+.0001")
    assert candidato.tipo == "posible_contacto" and candidato.valor >= .0001
    assert "no certifica" in candidato.mensaje


def test_cruce_descubierto_solo_se_clasifica():
    """Una región negativa no vista en la malla entrega un cruce evaluado, sin llamar al motor."""
    candidato = _refinar("(x-.125)**2-.001")
    assert candidato.tipo == "cruce"
    assert candidato.evidencia_contacto.motivo == "cruce"
    funcion = compilar("(x-.125)**2-.001")
    assert math.copysign(1, funcion(candidato.intervalo[0])) != math.copysign(1, funcion(candidato.intervalo[1]))


def test_fallo_auxiliar_no_es_cero_y_conserva_consumo():
    """Una división inválida en un sondeo se conserva como segmento inválido y cuenta ambas muestras."""
    candidato = _refinar("(x-.02)**2/((x*x-.0625)**2)")
    assert candidato.tipo == "segmento_invalido" and candidato.mensaje
    assert candidato.evidencia_contacto.evaluaciones == 2
    assert candidato.evidencia_contacto.motivo == "segmento_invalido"
    json.dumps(asdict(candidato), allow_nan=False)


def test_precision_sin_avance_no_ejecuta_sondeos():
    """Si no caben dos puntos interiores distintos se detiene sin repetir evaluaciones."""
    centro = 1e16
    muestras = (MuestraExploracion(centro - 2, 1), MuestraExploracion(centro, .01), MuestraExploracion(centro + 2, 1))
    llamadas = []
    candidato, = refinar_contacto(EntradaExploracion("x", centro - 2, centro + 2, 2),
                                 lambda abscisa: llamadas.append(abscisa), muestras, 24)
    assert llamadas == [] and candidato.evidencia_contacto.evaluaciones == 0
    assert candidato.evidencia_contacto.motivo == "precision"


@pytest.mark.parametrize("presupuesto,esperadas", [(0, 0), (1, 0), (2, 2), (23, 22), (24, 24), (25, 24), (512, 24)])
def test_presupuesto_individual_sin_sondeos_parciales(presupuesto, esperadas):
    """Reserva dos evaluaciones por paso y nunca supera doce refinamientos por contacto."""
    evidencia = _refinar("(x-.1)**2", presupuesto).evidencia_contacto
    assert evidencia.evaluaciones == esperadas and evidencia.refinamientos == esperadas // 2
    assert evidencia.motivo == ("presupuesto_global" if presupuesto < 24 else "limite_refinamientos")


@pytest.mark.parametrize("presupuesto", [-1, True, 1.5, 513, float("inf"), None])
def test_presupuesto_auxiliar_invalido_antes_de_evaluar(presupuesto):
    """El ayudante no trunca ni silencia presupuestos fuera del contrato global."""
    with pytest.raises(ValueError, match="presupuesto"):
        _refinar("(x-.1)**2", presupuesto)
