from src.ai.contexto import describir_matriz, generar_nota_ventana, ContextoIA, EstadoContexto


def test_nota_ventana_matriz_pequena():
    """La matriz pequeña no necesita una nota de recorte."""
    filas = [[str(i * 3 + j + 1) for j in range(3)] for i in range(3)]
    descripcion = describir_matriz(filas)
    assert "ventana" not in descripcion
    assert generar_nota_ventana(descripcion) is None


def test_nota_ventana_matriz_50x50():
    """La matriz grande informa de la ventana incluida en el contexto."""
    filas = [["1" for _ in range(50)] for _ in range(50)]
    descripcion = describir_matriz(filas)
    assert "ventana" in descripcion
    assert descripcion["ventana"] == [6, 6]
    nota = generar_nota_ventana(descripcion)
    assert nota == "ventana 6×6 de 50×50"


def test_nota_ventana_multiples_matrices_selecciona_mayor():
    """La nota representa la mayor de las matrices del contexto."""
    pequena = describir_matriz([["1"] * 3 for _ in range(3)])
    mediana = describir_matriz([["1"] * 12 for _ in range(12)])
    grande = describir_matriz([["1"] * 50 for _ in range(50)])

    nota = generar_nota_ventana(pequena, mediana, grande)
    assert nota == "ventana 6×6 de 50×50"

    nota_mediana = generar_nota_ventana(pequena, mediana)
    assert nota_mediana == "ventana 6×6 de 12×12"


def test_nota_ventana_contexto_vacio():
    """El contexto vacío conserva la respuesta esperada de la nota."""
    assert generar_nota_ventana() is None
    assert generar_nota_ventana({}) is None
    assert generar_nota_ventana(None) is None


def test_pildora_contexto_con_nota_ventana():
    """La píldora incorpora la nota de ventana cuando corresponde."""
    contexto = ContextoIA(
        herramienta="inversa",
        vista="Matriz Inversa",
        etiqueta="A (50×50)",
        entrada={},
        estado=EstadoContexto(nota_ventana="ventana 6×6 de 50×50")
    )
    assert contexto.nota_ventana == "ventana 6×6 de 50×50"
