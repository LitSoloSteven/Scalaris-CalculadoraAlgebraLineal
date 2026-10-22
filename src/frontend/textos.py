"""Catálogo centralizado de textos y mensajes de interfaz de Scalaris."""

MENSAJE_ANTI_REBOTE_GLOSA = "Espera un momento antes de enviar otra pregunta."

NOMBRE_SELECTOR_VECTORES = "Operaciones con vectores"
OPCIONES_OPERACIONES_VECTORES = (
    ('suma_resta', 'Suma / Resta', 'Suma / Resta'),
    ('escalar', 'Escalar × Vector', 'Escalar × Vector'),
    ('combinacion_lineal', 'Combinación lineal', 'Combinación lineal'),
    ('independencia', 'Independencia', 'Independencia lineal'),
)

NOMBRE_SELECTOR_DETERMINANTES = "Método para calcular el determinante"
DETERMINANTES_DESCRIPCION = "Cofactores o eliminación con pivoteo, con aritmética exacta."
OPCIONES_METODOS_DETERMINANTES = (
    ('laplace', 'Cofactores', 'Cofactores, expansión de Laplace'),
    ('lu', 'Eliminación con pivoteo', 'Eliminación con pivoteo'),
)
DETERMINANTES_USAR_RECOMENDADO = "Usar método recomendado"
DETERMINANTES_RECOMENDACION_VACIA = "Introduce una matriz para recibir una recomendación de método."
DETERMINANTES_RECOMENDACION_ESPERA = "Actualizando la recomendación de método…"
DETERMINANTES_RECOMENDACION_ERROR = "No pudimos recomendar un método. Revisa la matriz y vuelve a intentarlo."
DETERMINANTES_RECOMENDACION = "Método recomendado: {nombre}. {justificacion}"
DETERMINANTES_TITULO = "Determinantes"
DETERMINANTES_CALCULAR = "Calcular determinante"
DETERMINANTES_ORIENTACION = "Introduce una matriz cuadrada y calcula su determinante."
DETERMINANTES_CALCULANDO = "Calculando determinante…"
DETERMINANTES_ERROR = "No pudimos calcular el determinante. Revisa los datos y vuelve a intentarlo."
DETERMINANTES_VALOR = "Determinante: {valor}"
DETERMINANTES_SINGULAR = "La matriz es singular."
HISTORIAL_DETERMINANTE_CALCULADO = "Calculado"
HISTORIAL_DETERMINANTE_DETALLE = "det = {determinante}. Método: {metodo}"
VISTA_PREVIA_LIMITE = "Vista previa disponible hasta {dimension}×{dimension}."
VISTA_PREVIA_ERROR = "No se pudo generar la vista previa. Revisa la matriz."

LIMPIAR = "Limpiar"
LIMPIEZA_CANCELAR = "Cancelar"
LIMPIEZA_TITULO = "¿Vaciar datos?"
LIMPIEZA_DESCRIPCION = "Se eliminarán los datos."
LIMPIEZA_SIN_DATOS = "No hay datos que limpiar."
LIMPIEZA_VISUALIZAR = "Visualizar"
LIMPIEZA_ESTADO_BASES = "Ingresa un número y pulsa Convertir."
LIMPIEZA_ESTADO_ROMANOS = "Ingresa dos operandos romanos y pulsa Calcular."

MENSAJE_SECRETO_DESARROLLO_INSEGURO = "STORAGE_SECRET ausente. Usando secreto de desarrollo (inseguro)."
MENSAJE_ERROR_PRODUCCION_SIN_SECRETO = "ERROR CRÍTICO: SCALARIS_ENV es production pero falta STORAGE_SECRET."
