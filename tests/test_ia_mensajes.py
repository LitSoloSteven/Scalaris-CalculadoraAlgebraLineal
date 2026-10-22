"""Filtrado de historial y construcción de mensajes para el proveedor de IA."""
from src.ai.mensajes import construir_mensajes, recortar_historial

def test_recorte_historial():
    """El historial mantiene la cantidad y el orden de mensajes esperados."""
    historial = [
        {"texto": "1", "enviado": True},
        {"texto": "2", "error": True},
        {"texto": "3", "enviado": False}
    ]
    recortados = recortar_historial(historial)
    assert len(recortados) == 2
    assert recortados[0]["content"] == "1"
    assert recortados[1]["content"] == "3"

def test_construccion_mensajes():
    """Los mensajes conservan sus roles y la pregunta final."""
    historial = [{"texto": "hola", "enviado": True}]
    mensajes = construir_mensajes(historial, "adios", "[CONTEXTO]123[/CONTEXTO]", respuesta_simple=True)
    
    assert len(mensajes) == 3
    assert mensajes[0]["role"] == "system"
    assert mensajes[1]["content"] == "hola"
    assert mensajes[2]["role"] == "user"
    assert "[CONTEXTO]123[/CONTEXTO]" in mensajes[2]["content"]
    assert "adios" in mensajes[2]["content"]
    assert "más simple" in mensajes[2]["content"]
