"""Restauración completa de capturas de modelos sin ejecutar cálculos."""
from src.frontend.componentes.captura_modelos import llenar_entradas
from src.frontend import textos_transformaciones as textos


def cargar_captura_modelo(vista, captura: dict) -> None:
    """Restaura matriz y campos auxiliares, adapta dimensiones e invalida resultados."""
    leontief = vista.herramienta_modelo == "leontief"
    matriz = captura["matriz_coeficientes" if leontief else "matriz_transformacion"]
    if leontief:
        vista.numero_sectores = len(matriz)
    else:
        vista.filas, vista.columnas = len(matriz), len(matriz[0])
        aplicacion = "vector_original" in captura
        vista.selector_modo.set_value(textos.MODO_APLICACION if aplicacion else textos.MODO_ANALISIS)
        vista.selector_tipo_objeto.set_value(captura.get("tipo_objeto", "vector"))
    vista._generar_cuadricula()
    if leontief:
        vista._generar_entradas_demanda()
        vista._generar_entradas_sectores()
        llenar_entradas(vista.entradas_demanda, captura["vector_demanda"])
        llenar_entradas(vista.entradas_sectores, captura.get("nombres_sectores", []))
    else:
        vista._generar_entradas_variables()
        llenar_entradas(vista.entradas_variables, captura.get("nombres_variables", []))
        llenar_entradas(vista.entradas_vector_original, captura.get("vector_original", []))
    for entradas, valores in zip(vista.entradas_coeficientes, matriz):
        llenar_entradas(entradas, valores)
    vista._restablecer_resultados()
