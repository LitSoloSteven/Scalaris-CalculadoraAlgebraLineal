"""Presupuesto total, recorte matricial y aislamiento con claves canónicas españolas."""
from copy import deepcopy
import json

import pytest

from src.ai.contexto import CapturaPaso, ContextoIA, EstadoContexto, ReferenciaPaso, serializar_contexto
from src.ai.estrategias_recorte import _reducir_elemento_entrada


@pytest.mark.parametrize("limite", [120, 180, 400, 1200, 4000])
def test_presupuesto_con_dimensiones_y_foco_espanoles(limite):
    """El bloque respeta el límite sin mutar entradas ni las dimensiones originales."""
    matriz = {"filas": 12, "columnas": 12, "datos": [["123456789/987654321"] * 12 for _ in range(12)]}
    captura = CapturaPaso({"1": ["1/3"] * 20}, {"1": ["2/3"] * 20}, (1, 20), {"datos": "x" * 5000})
    contexto = ContextoIA("matrices", "Matrices", "Ejercicio", {"A": matriz},
                         EstadoContexto(resultado={"estado": "EXITO", "pasos": ["x" * 5000]},
                                        foco=ReferenciaPaso(1, 2, "normalizacion", "Dividir", captura)))
    copia = deepcopy(contexto)
    bloque = serializar_contexto(contexto, maximo_caracteres=limite)
    datos = json.loads(bloque[len("[CONTEXTO]\n"):-len("\n[/CONTEXTO]")])
    assert len(bloque) <= limite
    assert contexto == copia
    assert datos["herramienta"] == "matrices"
    assert datos["metadatos"]["truncado"] is True
    assert '"rows"' not in bloque and '"cols"' not in bloque


def test_recorte_reconoce_dimensiones_canonicamente():
    """La ventana se reduce y conserva filas/columnas originales."""
    matriz = {"filas": 5, "columnas": 6, "datos": [["1"] * 6 for _ in range(5)]}
    _reducir_elemento_entrada(matriz, 3)
    assert matriz == {"filas": 5, "columnas": 6, "datos": [["1"] * 3 for _ in range(3)], "ventana": [3, 3]}
