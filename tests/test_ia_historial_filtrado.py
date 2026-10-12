"""Filtrado previo al recorte y prioridades de contenido del historial de Glosa."""
from copy import deepcopy
import pytest

from src.ai.mensajes import recortar_historial


@pytest.mark.parametrize("limite,esperados", [(2, ["2", "3"]), (0, ["1", "2", "3"]), (-1, ["2", "3"]), (8, ["1", "2", "3"])])
def test_recorte_aplica_slice_despues_de_filtrar_sin_mutar(limite, esperados):
    """El límite se aplica a mensajes válidos conservando la semántica de cero y negativos."""
    historial = [
        {"text": "1", "sent": True}, {"text": "", "sent": False},
        {"text": "2", "sent": False}, {"text": "Error", "error": True},
        {"text": "3", "sent": True}, {"content": "   "},
    ]
    copia = deepcopy(historial)
    resultado = recortar_historial(historial, limite)
    assert [mensaje["content"] for mensaje in resultado] == esperados
    assert historial == copia


@pytest.mark.parametrize("mensaje,esperado", [
    ({"text": " Principal ", "content": "Secundario", "sent": True}, {"role": "user", "content": "Principal"}),
    ({"text": "", "content": "Secundario"}, None),
    ({"text": None, "content": " Alternativo ", "role": "assistant"}, {"role": "assistant", "content": "Alternativo"}),
    ({"content": "Texto", "sent": True, "role": None}, {"role": None, "content": "Texto"}),
    ({"text": "Texto", "error": True}, None),
    ({}, None),
])
def test_prioridad_de_texto_y_rol_se_conserva(mensaje, esperado):
    """El rol explícito y la presencia de texto tienen la prioridad histórica."""
    assert recortar_historial([mensaje]) == ([] if esperado is None else [esperado])


@pytest.mark.parametrize("contenido", [0, False, ["texto"]])
def test_contenido_no_textual_conserva_excepcion(contenido):
    """El contrato histórico exige cadenas y no transforma contenido de otros tipos."""
    with pytest.raises(AttributeError):
        recortar_historial([{"text": contenido}])
