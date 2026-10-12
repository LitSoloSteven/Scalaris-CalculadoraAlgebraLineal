"""Construcción de preguntas de explicación de pasos algebraicos."""
from src.ai.mensajes import construir_pregunta_explicar_paso


def test_pregunta_incluye_paso_operacion_y_proposito():
    """La pregunta identifica el paso y solicita una explicación de su propósito."""
    pregunta = construir_pregunta_explicar_paso("eliminacion", 2, 5, "Fila 2 = Fila 2 - (3)·Fila 1")
    assert "Paso 2 de 5" in pregunta
    assert "Fila 2 = Fila 2 - (3)·Fila 1" in pregunta
    assert "qué se busca" in pregunta.lower() or "por qué" in pregunta.lower() or "qué cambia" in pregunta.lower()
