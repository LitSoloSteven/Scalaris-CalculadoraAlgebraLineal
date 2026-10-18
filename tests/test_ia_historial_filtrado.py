"""Filtrado previo al recorte y prioridades de contenido del historial de Glosa."""
from copy import deepcopy
import pytest

from src.ai.mensajes import recortar_historial


@pytest.mark.parametrize("limite,esperados", [(2, ["2", "3"]), (0, ["1", "2", "3"]), (-1, ["2", "3"]), (8, ["1", "2", "3"])])
def test_recorte_aplica_slice_despues_de_filtrar_sin_mutar(limite, esperados):
    """El límite se aplica a mensajes válidos conservando la semántica de cero y negativos."""
    historial = [
        {"texto": "1", "enviado": True}, {"texto": "", "enviado": False},
        {"texto": "2", "enviado": False}, {"texto": "Error", "error": True},
        {"texto": "3", "enviado": True}, {"content": "   "},
    ]
    copia = deepcopy(historial)
    resultado = recortar_historial(historial, limite)
    assert [mensaje["content"] for mensaje in resultado] == esperados
    assert historial == copia


@pytest.mark.parametrize("mensaje,esperado", [
    ({"texto": " Principal ", "content": "Secundario", "enviado": True}, None),
    ({"texto": "", "content": "Secundario"}, None),
    ({"texto": None, "content": " Alternativo ", "role": "assistant"}, None),
    ({"content": "Texto", "enviado": True, "role": None}, None),
    ({"texto": "Texto", "error": True}, None),
    ({}, None),
])
def test_prioridad_de_texto_y_rol_se_conserva(mensaje, esperado):
    """Los formatos alternativos se rechazan sin sustituir el texto canónico."""
    assert recortar_historial([mensaje]) == ([] if esperado is None else [esperado])


@pytest.mark.parametrize("contenido", [0, False, ["texto"]])
def test_contenido_no_textual_conserva_excepcion(contenido):
    """El contrato histórico exige cadenas y no transforma contenido de otros tipos."""
    with pytest.raises(AttributeError):
        recortar_historial([{"texto": contenido}])
