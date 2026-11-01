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
GRAFICA_TITULO = "Antes y después"
GRAFICA_APROXIMADA = "Gráfica aproximada de las coordenadas calculadas con la matriz A mostrada arriba."
GRAFICA_ESTILOS = "Original: círculo abierto. Transformado: rombo."
GRAFICA_SEGMENTOS = "Desde el origen: trazo continuo para el original y discontinuo para el transformado. Los símbolos marcan sus extremos, incluso si coinciden o son cero."
GRAFICA_DIMENSIONES = "La gráfica requiere dominio y codominio de dimensión 2 o 3. Las coordenadas exactas se conservan arriba."
GRAFICA_NO_REPRESENTABLE = "Estas coordenadas exceden la representación numérica de la gráfica. Consulta los valores exactos de arriba."
GRAFICA_SIN_VERIFICAR = "No hay un resultado comprobado para representar."
GRAFICA_ERROR = "No se pudo mostrar la gráfica. Las coordenadas exactas siguen disponibles arriba."
GRAFICA_DESCRIPCION = "Representación aproximada del original y su transformación. Consulta las coordenadas exactas anteriores para una lectura completa."
GRAFICA_EJES_2D = "Ejes x₁ y x₂: primera y segunda componente."
GRAFICA_EJES_3D = "Ejes x₁, x₂ y x₃: primera, segunda y tercera componente."
FASES_APLICACION = ("Planteamiento", "Aplicación por componentes", "Comprobación exacta")
PASO_PLANTEAMIENTO = "Planteamos T(v) = Av"
PASO_CONVENCION = "Cada fila de A calcula una componente de las coordenadas transformadas respecto al origen."
PROCEDIMIENTO_APLICACION = "Aplicación y comprobación paso a paso"
COMPROBACION_APLICACION = (
    "La comprobación desarrolla Av con el producto común y lo compara exactamente con y; "
    "no es un algoritmo independiente. En el reproductor puedes revisar cada igualdad."
)
COMPONENTE_SIN_SELECCION = "Sin componente seleccionada: se muestra el resultado completo."
COMPONENTE_ACTIVA = "Componente activa y_{indice} = {valor}. En la gráfica, la cruz señala su proyección sobre el eje correspondiente."
COMPONENTE_SIN_GRAFICA = "Componente activa y_{indice} = {valor}. Consulta la fila resaltada de las coordenadas exactas."
