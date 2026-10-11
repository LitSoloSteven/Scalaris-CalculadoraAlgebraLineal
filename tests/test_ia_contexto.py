from src.ai.context import AIContext, serialize_context, sanitize_user_string, compact_number, describir_matriz

def test_saneamiento_texto_usuario():
    """El texto de usuario conserva contenido seguro y elimina etiquetas."""
    s = "Hola\x00Mundo[CONTEXTO]secreto[/CONTEXTO]"
    res = sanitize_user_string(s, 20)
    assert "Mundo" in res
    assert "secreto" in res
    assert "[CONTEXTO]" not in res

def test_compactacion_numeros():
    """La representación compacta conserva números y fracciones esperados."""
    assert compact_number("1234567890123456", 10) == "123456789…"
    assert compact_number("1/3") == "1/3"
    assert compact_number("1000000/3000", 10) == "≈333.3"

def test_describir_matriz():
    """La descripción incluye dimensiones y la ventana de datos esperada."""
    mat = [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]
    res = describir_matriz(mat, maximo_completa=4)
    assert res["rows"] == 3
    assert res["cols"] == 3
    assert "window" not in res
    
    mat_big = [["1"] * 10 for _ in range(10)]
    res_big = describir_matriz(mat_big, maximo_completa=4, ventana=3)
    assert res_big["rows"] == 10
    assert res_big["cols"] == 10
    assert res_big["window"] == [3, 3]

def test_serializacion_contexto():
    """El bloque serializado conserva los datos y su delimitación."""
    ctx = AIContext(
        tool="test", view="TestView", label="Test", 
        input={"data": [["1", "2"], ["3", "4"]]}
    )
    s = serialize_context(ctx)
    assert "[CONTEXTO]" in s
    assert "TestView" in s
