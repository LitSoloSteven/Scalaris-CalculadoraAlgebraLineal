"""Textos y opciones de captura de la aplicación de transformaciones lineales."""
MODO_ANALISIS = "analisis"
MODO_APLICACION = "aplicacion"
OPCIONES_MODO = (
    (MODO_ANALISIS, "Analizar matriz", "Analizar núcleo e imagen de la matriz"),
    (MODO_APLICACION, "Aplicar matriz", "Aplicar la matriz a un punto o vector"),
)
OPCIONES_OBJETO = (
    ("vector", "Vector", "Transformar un vector columna"),
    ("punto", "Punto", "Transformar las coordenadas de un punto"),
)
TITULO = "Transformaciones lineales"
DESCRIPCION = "Aplica una matriz o explora su núcleo, imagen, rango y nulidad."
AVISO_ACADEMICO = (
    "Alcance académico pendiente de confirmación: el calendario de P5 contempla "
    "aplicaciones matriciales y la rúbrica menciona subespacios. Aquí puedes explorar ambos contenidos."
)
CONVENCION = (
    "Las coordenadas se interpretan respecto al origen y se multiplican como un vector columna: "
    "T(v) = Av. Esta transformación no incluye traslaciones."
)
TITULO_CAPTURA = "Coordenadas originales"
AYUDA_CAPTURA = "Ingresa una componente por fila. Puedes pegar una columna de valores."
APLICAR = "Aplicar matriz"
ANALIZAR = "Analizar"
ESTADO_APLICACION = "Ingresa la matriz A y las coordenadas originales; después presiona Aplicar matriz."
ESTADO_ANALISIS = "Ingresa la matriz A y presiona Analizar."
RESULTADO_TITULO = "Transformación aplicada"
ERROR_COMPROBACION = "La comprobación no coincide con el resultado. Revisa los datos y vuelve a calcular."
TITULOS_COORDENADAS = {
    "vector": ("Vector original", "Vector transformado"),
    "punto": ("Punto original", "Punto transformado"),
}
COORDENADAS_EXACTAS = "Coordenadas exactas; las fracciones conservan su valor racional."
TITULO_EJEMPLOS = "Ejemplos de aplicación"
