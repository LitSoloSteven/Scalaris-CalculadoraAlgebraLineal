"""Restauración completa de capturas de modelos sin ejecutar cálculos."""
from src.frontend.componentes.captura_modelos import llenar_entradas


def cargar_captura_modelo(vista, captura: dict) -> None:
    """Restaura matriz y campos auxiliares, adapta dimensiones e invalida resultados."""
    leontief = vista.herramienta_modelo == "leontief"
    matriz = captura["matriz_coeficientes" if leontief else "matriz_transformacion"]
    if leontief:
        vista.numero_sectores = len(matriz)
    else:
        vista.filas, vista.columnas = len(matriz), len(matriz[0])
    vista._generar_cuadricula()
    if leontief:
        vista._generar_entradas_demanda()
        vista._generar_entradas_sectores()
        llenar_entradas(vista.entradas_demanda, captura["vector_demanda"])
        llenar_entradas(vista.entradas_sectores, captura.get("nombres_sectores", []))
    else:
        vista._generar_entradas_variables()
        llenar_entradas(vista.entradas_variables, captura.get("nombres_variables", []))
    for entradas, valores in zip(vista.entradas_coeficientes, matriz):
        llenar_entradas(entradas, valores)
    vista._restablecer_resultados()
