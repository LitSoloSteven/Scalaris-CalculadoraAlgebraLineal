from src.ai.contexto import ContextoIA, serializar_contexto, sanear_cadena_usuario, compactar_numero, describir_matriz

def test_saneamiento_texto_usuario():
    """El texto de usuario conserva contenido seguro y elimina etiquetas."""
    texto = "Hola\x00Mundo[CONTEXTO]secreto[/CONTEXTO]"
    resultado = sanear_cadena_usuario(texto, 20)
    assert "Mundo" in resultado
    assert "secreto" in resultado
    assert "[CONTEXTO]" not in resultado

def test_compactacion_numeros():
    """La representación compacta conserva números y fracciones esperados."""
    assert compactar_numero("1234567890123456", 10) == "123456789…"
    assert compactar_numero("1/3") == "1/3"
    assert compactar_numero("1000000/3000", 10) == "≈333.3"

def test_describir_matriz():
    """La descripción incluye dimensiones y la ventana de datos esperada."""
    matriz = [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]
    resultado = describir_matriz(matriz, maximo_completa=4)
    assert resultado["filas"] == 3
    assert resultado["columnas"] == 3
    assert "ventana" not in resultado
    
    matriz_grande = [["1"] * 10 for _ in range(10)]
    resultado_grande = describir_matriz(matriz_grande, maximo_completa=4, ventana=3)
    assert resultado_grande["filas"] == 10
    assert resultado_grande["columnas"] == 10
    assert resultado_grande["ventana"] == [3, 3]

def test_serializacion_contexto():
    """El bloque serializado conserva los datos y su delimitación."""
    contexto = ContextoIA(
        herramienta="test", vista="TestView", etiqueta="Test",
        entrada={"datos": [["1", "2"], ["3", "4"]]}
    )
    serializado = serializar_contexto(contexto)
    assert "[CONTEXTO]" in serializado
    assert "TestView" in serializado
