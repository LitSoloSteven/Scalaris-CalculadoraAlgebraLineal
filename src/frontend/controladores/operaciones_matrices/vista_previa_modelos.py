"""Vista previa de coeficientes validada por el dominio sin resolver el modelo."""
from src.backend.resolutores.operaciones_matrices.captura_modelos import parsear_matriz_modelo
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from .contexto_modelos import capturar_modelo


def preparar_vista_previa_modelo(vista) -> str:
    """Devuelve la matriz capturada en LaTeX; propaga ValueError si hay celdas inválidas."""
    leontief = vista.herramienta_modelo == "leontief"
    captura = capturar_modelo(vista)
    datos = captura["matriz_coeficientes" if leontief else "matriz_transformacion"]
    etiqueta = "C" if leontief else "A"
    matriz = parsear_matriz_modelo(datos, etiqueta, cuadrada=leontief)
    return f"{etiqueta} = {matriz_a_latex(matriz)}"
