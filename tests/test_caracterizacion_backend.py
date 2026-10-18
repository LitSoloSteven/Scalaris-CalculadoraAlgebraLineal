"""Contratos completos con resultados literales de las familias algebraicas."""

import json
from pathlib import Path

import pytest

from tests.comun_caracterizacion_backend import ejecutar_caso

RAIZ_DATOS = Path(__file__).parent
CASOS = json.loads((RAIZ_DATOS / "casos_caracterizacion_backend.json").read_text(encoding="utf-8"))
RESULTADOS = json.loads((RAIZ_DATOS / "resultados_caracterizacion_backend.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("caso", CASOS, ids=lambda caso: caso["nombre"])
def test_caracterizacion_contratos_backend(caso):
    """Conserva campos, resultados, tipos, pasos, textos y errores de cada familia."""
    assert ejecutar_caso(caso) == RESULTADOS[caso["nombre"]]
