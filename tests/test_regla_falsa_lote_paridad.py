"""Paridad del adaptador de interfaz con el motor individual y el contrato de lote."""
import json
import math

import pytest

from src.frontend.controladores.regla_falsa import resolucion_multiple
from src.frontend.controladores.regla_falsa.ejecucion_ampliada import resolver_presentacion
from src.frontend.controladores.regla_falsa.presentacion_ampliada import etiqueta_configurada
from tests.comun_regla_falsa_vista import captura_regla_falsa


def _registro(identificador, intervalo, tipo="cruce", abscisa=None):
    return {"identificador": identificador, "candidato": {"tipo": tipo, "intervalo": intervalo,
                                                        "abscisa": abscisa, "valor": None}}


@pytest.mark.parametrize("tipo,parametro", [("residuo", "1e-6"), ("ancho", ".25"),
    ("decimales", "1"), ("relativo", "1"), ("iteraciones", "2")])
def test_adaptador_usa_una_sola_solicitud_y_preserva_el_resultado_por_criterio(monkeypatch, tipo, parametro):
    """Confronta cada criterio con la traza individual y cuenta las solicitudes de lote."""
    configuracion = captura_regla_falsa(expresion="x^3-x", criterio={"tipo": tipo, "parametro": parametro})
    candidatos = (_registro("izquierda", (-1.2, -.8)), _registro("derecha", (.8, 1.2)))
    llamadas = []
    original = resolucion_multiple.resolver_candidatos_regla_falsa

    def resolver(entrada):
        """Registra cada llamada del adaptador y delega al servicio real."""
        llamadas.append(entrada)
        return original(entrada)

    monkeypatch.setattr(resolucion_multiple, "resolver_candidatos_regla_falsa", resolver)
    lote = resolucion_multiple.resolver_lote({"configuracion": configuracion, "candidatos": candidatos})
    assert len(llamadas) == 1 and lote["estado"] == "LOTE_COMPLETADO"
    for registro, candidato in zip(lote["resultados"], candidatos, strict=True):
        inferior, superior = candidato["candidato"]["intervalo"]
        individual = resolver_presentacion({**configuracion, "extremo_izquierdo": inferior, "extremo_derecho": superior})
        assert registro["datos"]["resultado"] == individual["resultado"]
        assert registro["datos"]["ampliado"] == individual["ampliado"]
        assert registro["datos"]["resultado"]["metodo"] == "regla_falsa"
    json.dumps(lote, allow_nan=False)


@pytest.mark.parametrize("intervalo,limite,esperado", [((1, 2), "1", "LIMITE_ITERACIONES"),
    ((math.nextafter(math.sqrt(2), 0), math.sqrt(2)), "100", "ESTANCAMIENTO")])
def test_candidato_invalido_no_oculta_resultado_provisional(intervalo, limite, esperado):
    """Distingue un fallo individual de una aproximación provisional disponible para abrir."""
    configuracion = captura_regla_falsa(limite_iteraciones=limite, criterio={"tipo": "relativo", "parametro": "1e-30"})
    lote = resolucion_multiple.resolver_lote({"configuracion": configuracion,
        "candidatos": (_registro("invalido", (2, 1)), _registro("provisional", intervalo))})
    invalido, provisional = lote["resultados"]
    assert invalido["estado"] == "NO_APTO" and invalido["datos"] is None
    assert provisional["estado"] == esperado
    datos = provisional["datos"]
    assert datos["resultado"]["aproximacion"] is not None
    assert etiqueta_configurada(datos["resultado"], datos["ampliado"]) == "Aproximación provisional"
