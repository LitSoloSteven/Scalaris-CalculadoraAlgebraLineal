"""Mensajes de Glosa, serialización de contexto, huellas y modalidad de entrada."""
from fractions import Fraction

from src.ai.mensajes import construir_mensajes
from src.ai.contexto import serializar_contexto, ContextoIA, EstadoContexto, MAXIMO_CARACTERES_CONTEXTO
from src.ai.huellas import calcular_huella, esta_desactualizado
from src.frontend.componentes.glosa_sugerencias import _es_evento_teclado
from src.backend.modelos.matriz import Matriz

def test_mensajes_roles_y_pregunta():
    """El contexto y el historial se ordenan antes de la pregunta."""
    usuario = {"enviado": True, "texto": "¿Cómo se resuelve esto?"}
    asistente = {"enviado": False, "texto": "Se resuelve aplicando eliminación de Gauss."}
    pregunta = "¿Qué hago en el paso 2?"
    mensajes = construir_mensajes(historial=[usuario, asistente], pregunta=pregunta)
    roles = [mensaje["role"] for mensaje in mensajes]
    assert roles == ["system", "user", "assistant", "user"]
    for mensaje in mensajes:
        assert mensaje["content"].strip() != ""
    assert sum(pregunta in mensaje["content"] for mensaje in mensajes) == 1

def test_mensajes_con_historial_vacio():
    """La pregunta se construye también sin mensajes previos."""
    pregunta = "Hola Glosa"
    mensajes = construir_mensajes(historial=[], pregunta=pregunta)
    assert len(mensajes) == 2
    assert mensajes[0]["role"] == "system"
    assert mensajes[1]["role"] == "user"
    assert mensajes[1]["content"] == pregunta
    assert not any(mensaje["role"] == "assistant" for mensaje in mensajes)

def test_mensajes_filtran_vacios_y_errores():
    """El historial no envía contenido vacío ni errores del asistente."""
    historial = [
        {"enviado": True, "texto": "Mensaje válido 1"},
        {"enviado": False, "texto": ""},
        {"enviado": True, "texto": "   "},
        {"enviado": False, "texto": "Error ocurrió", "error": True},
        {"enviado": False, "texto": "Respuesta válida"}
    ]
    mensajes = construir_mensajes(historial=historial, pregunta="Nueva pregunta")
    roles = [mensaje["role"] for mensaje in mensajes]
    assert roles == ["system", "user", "assistant", "user"]
    for mensaje in mensajes:
        assert mensaje["content"].strip() != ""
        assert not mensaje.get("error", False)

def test_contexto_serializa_matriz_y_fraccion():
    """El contexto admite matrices y fracciones sin perder sus valores."""
    matriz = Matriz(2, 2, [[Fraction(1, 2), Fraction(3, 4)], [Fraction(5, 6), Fraction(7, 8)]])
    contexto = ContextoIA(
        herramienta="inversa",
        vista="inversa",
        etiqueta="Inversa 2×2",
        entrada={"filas": 2, "columnas": 2, "datos": [["1/2", "3/4"], ["5/6", "7/8"]]},
        estado=EstadoContexto(resultado={"matriz": matriz, "det": Fraction(1, 16), "custom": Fraction(2, 3)})
    )
    serializado = serializar_contexto(contexto)
    assert isinstance(serializado, str)
    assert "[CONTEXTO]" in serializado
    assert len(serializado) <= MAXIMO_CARACTERES_CONTEXTO
    assert "filas" in serializado

def test_huella_y_deteccion_contexto_obsoleto():
    """La huella distingue entradas actuales y resultados obsoletos."""
    primera = {"alpha": 1, "beta": [1, 2, 3], "gamma": {"x": "a", "y": "b"}}
    equivalente = {"gamma": {"y": "b", "x": "a"}, "beta": [1, 2, 3], "alpha": 1}
    assert calcular_huella(primera) == calcular_huella(equivalente)
    huella = calcular_huella(primera)
    assert esta_desactualizado(primera, None) is False
    assert esta_desactualizado(equivalente, huella) is False
    distinta = {"alpha": 2, "beta": [1, 2, 3], "gamma": {"x": "a", "y": "b"}}
    assert esta_desactualizado(distinta, huella) is True

def test_deteccion_entrada_teclado():
    """El cliente detecta teclado para aplicar la interacción instantánea."""
    assert _es_evento_teclado({"detail": 0}) is True
    assert _es_evento_teclado(0) is True
    assert _es_evento_teclado([{"detail": 0}]) is True
    assert _es_evento_teclado([0]) is True
    
    assert _es_evento_teclado({"detail": 1}) is False
    assert _es_evento_teclado(1) is False
    assert _es_evento_teclado([{"detail": 1}]) is False
    assert _es_evento_teclado([1]) is False
    assert _es_evento_teclado(None) is False
