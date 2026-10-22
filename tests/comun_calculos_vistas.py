"""Entradas mínimas y comprobaciones matemáticas para vistas montadas realmente."""
from fractions import Fraction
from nicegui import ui


async def calcular_minimo(herramienta: str, vista) -> None:
    """Despacha un escenario válido y comprueba el resultado de su manejador real."""
    calculos = {
        "sistemas": calcular_sistema, "vectores": calcular_vectores,
        "matrices": calcular_matrices, "inversa": calcular_inversa,
        "leontief": calcular_leontief, "transformaciones": calcular_transformacion,
        "bases": calcular_bases, "romanos": calcular_romanos, "visualizador": calcular_geometria,
    }
    await calculos[herramienta](vista)


async def calcular_sistema(vista) -> None:
    """Resuelve un sistema identidad mediante su botón real de cálculo."""
    vista.pestanas_modo.set_value("Matriz")
    vista.cuadricula._cache_coeficientes = {(0, 0): "1", (1, 1): "1", (2, 2): "1"}
    vista.cuadricula._cache_independientes = {0: "1", 1: "2", 2: "3"}
    vista.cuadricula.generar_cuadricula()
    await vista.resolver_sistema(ui.button("Resolver prueba"))
    resultado = vista.ultimo_resultado
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion"] == ["1", "2", "3"]


async def calcular_vectores(vista) -> None:
    """Suma dos vectores con una fracción exacta desde la captura montada."""
    for vector, valores in zip(vista.panel_suma_resta.vectores.values(), [["1/3", "0", "0"], ["2/3", "0", "0"]]):
        vector["celdas"] = dict(enumerate(valores))
    await vista.calcular()
    assert vista.resultado_actual["estado"] != "ERROR"
    assert vista.resultado_actual["matriz_resultado"]["datos"] == [["1"], ["0"], ["0"]]


async def calcular_matrices(vista) -> None:
    """Evalúa una matriz fraccionaria mediante extracción y serialización reales."""
    vista.panel_captura_matrices.cargar_datos({"A": [["1/3"]]})
    vista.entrada_expresion.set_value("A + A")
    await vista.evaluar_expresion(ui.button("Evaluar prueba"))
    assert vista.ultimo_resultado["estado"] == "EXITO"
    assert vista.ultimo_resultado["pasos_segmento"]
    assert vista.ultimo_resultado["matriz_resultado"]["datos"] == [["2/3"]]


async def calcular_inversa(vista) -> None:
    """Invierte una matriz diagonal desde el panel cuadrado real."""
    vista.panel_matriz_cuadrada.cargar_matriz([["2", "0"], ["0", "3"]])
    await vista.calcular(ui.button("Invertir prueba"))
    assert vista.ultimo_resultado["estado"] == "EXITO"
    assert vista.ultimo_resultado["inversa"].datos == [[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(1, 3)]]


async def calcular_leontief(vista) -> None:
    """Calcula una economía sin consumo intermedio y verifica su renderizado."""
    for entrada, valor in zip(vista.entradas_demanda, ["1/3", "2/3"]): entrada.set_value(valor)
    await vista._calcular(ui.button("Calcular prueba"))
    assert vista.ultimo_resultado["estado"] == "EXITO"
    assert vista.ultimo_resultado["vector_produccion"] == ["1/3", "2/3"]
    assert vista.ultimo_resultado["vector_demanda"] == ["1/3", "2/3"]
    assert vista.ultimo_resultado["hawkins_simon"]["menores_principales"]
    comprobar_presentacion_leontief(vista)


def comprobar_presentacion_leontief(vista) -> None:
    """Exige tarjetas, sectores, demanda y menores en el contenedor del resultado."""
    elementos = list(vista.contenedor_resultados.descendants())
    etiquetas = {elemento.text for elemento in elementos if isinstance(elemento, ui.label)}
    assert not any("Error inesperado" in texto for texto in etiquetas)
    assert {"Sector 1", "Sector 2", "Análisis Sectorial", "1/3", "2/3", "0"} <= etiquetas
    assert "Condición de Hawkins-Simon: SATISFECHA ✓" in etiquetas
    contenido = "\n".join(elemento.content for elemento in elementos if isinstance(elemento, ui.html))
    for fraccion in ("1/3", "2/3"):
        assert f"Demanda final: <b>{fraccion}</b>" in contenido
        assert f"Producción total: {fraccion}" in contenido
    assert "Δ<sub>1</sub> = 1" in contenido
    assert "Δ<sub>2</sub> = 1" in contenido


async def calcular_transformacion(vista) -> None:
    """Analiza la identidad bidimensional desde las entradas reales de la vista."""
    for i, fila in enumerate(vista.entradas_coeficientes):
        for j, entrada in enumerate(fila): entrada.set_value("1" if i == j else "0")
    await vista._analizar(ui.button("Analizar prueba"))
    assert vista.ultimo_resultado["estado"] == "EXITO"
    assert vista.ultimo_resultado["rango"] == 2


async def calcular_bases(vista) -> None:
    """Convierte dos decimal a binario con el controlador activo de la vista."""
    vista.entrada_valor.set_value("2")
    await vista._convertir_boton()
    assert vista.tiene_resultado
    assert vista.resultados["binario"].replace(" ", "") == "10"


async def calcular_romanos(vista) -> None:
    """Suma I e I mediante el manejador de la calculadora romana."""
    vista.entrada_a.set_value("I")
    vista.entrada_b.set_value("I")
    resultado = vista.operar_romanos()
    if hasattr(resultado, "__await__"): await resultado
    assert vista.ultimo_resultado.resultado_romano == "II"


async def calcular_geometria(vista) -> None:
    """Construye una figura desde un sistema identidad capturado por la escena real."""
    vista.cuadricula._cache_coeficientes = {(0, 0): "1", (1, 1): "1"}
    vista.cuadricula._cache_independientes = {0: "1", 1: "2"}
    vista.cuadricula.generar_cuadricula()
    await vista._actualizar_figura()
    assert vista.ultimo_resultado["estado"] == "EXITO"
    assert vista._elemento_plotly is not None
