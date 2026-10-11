import pytest
from src.ai.prompts import build_messages, trim_history

def test_recorte_historial():
    """El historial mantiene la cantidad y el orden de mensajes esperados."""
    hist = [
        {"text": "1", "sent": True},
        {"text": "2", "error": True},
        {"text": "3", "sent": False}
    ]
    trimmed = trim_history(hist)
    assert len(trimmed) == 2
    assert trimmed[0]["content"] == "1"
    assert trimmed[1]["content"] == "3"

def test_construccion_mensajes():
    """Los mensajes conservan sus roles y la pregunta final."""
    hist = [{"text": "hola", "sent": True}]
    msgs = build_messages(hist, "adios", "[CONTEXTO]123[/CONTEXTO]", simpler=True)
    
    assert len(msgs) == 3
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"] == "hola"
    assert msgs[2]["role"] == "user"
    assert "[CONTEXTO]123[/CONTEXTO]" in msgs[2]["content"]
    assert "adios" in msgs[2]["content"]
    assert "más simple" in msgs[2]["content"]
