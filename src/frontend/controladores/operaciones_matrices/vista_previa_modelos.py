"""Vista previa de coeficientes validada por el dominio sin resolver el modelo."""
from src.backend.resolutores.operaciones_matrices.captura_modelos import parsear_matriz_modelo
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.utilidades.validadores import validar_dimensiones_multiplicacion
from .contexto_modelos import capturar_modelo


def preparar_vista_previa_modelo(vista) -> str:
    """Devuelve la matriz capturada en LaTeX; propaga ValueError si hay celdas inválidas."""
    leontief = vista.herramienta_modelo == "leontief"
    captura = capturar_modelo(vista)
    if "vector_original" in captura:
        return preparar_vista_previa_aplicacion(captura)
    datos = captura["matriz_coeficientes" if leontief else "matriz_transformacion"]
    etiqueta = "C" if leontief else "A"
    matriz = parsear_matriz_modelo(datos, etiqueta, cuadrada=leontief)
    return f"{etiqueta} = {matriz_a_latex(matriz)}"


def preparar_vista_previa_aplicacion(captura: dict) -> str:
    """Formatea Av sin calcular; propaga errores de captura o dimensiones incompatibles."""
    matriz = parsear_matriz_modelo(captura["matriz_transformacion"], "A")
    vector = parsear_matriz_modelo([[valor] for valor in captura["vector_original"]], "v")
    validar_dimensiones_multiplicacion(matriz, vector)
    return rf"T(v)=Av={matriz_a_latex(matriz)}{matriz_a_latex(vector)}"
