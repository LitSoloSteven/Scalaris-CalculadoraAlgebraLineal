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
DETERMINANTES_INVERTIBLE = "Matriz invertible"
DETERMINANTES_ESTADO_SINGULAR = "Matriz singular"
DETERMINANTES_AVISO_SINGULAR = "det(A) = 0: las columnas son dependientes y A no tiene inversa."
DETERMINANTES_PASOS = "Pasos del determinante"
DETERMINANTES_AYUDA = (
    "Compara la matriz de cada paso con la anterior y recorre el índice por fases.",
    "En cofactores, conserva los índices originales al eliminar una fila y una columna.",
    "En eliminación, cada intercambio cambia el signo; sumar un múltiplo de otra fila lo conserva.",
)
DETERMINANTES_LEYENDA = ("planteamiento", "menor", "inicial", "pivote", "intercambio", "eliminacion", "final")
DETERMINANTES_PLANTEAMIENTO = "Planteamiento"
DETERMINANTES_MENOR = "Menores y cofactores · columna {columna}"
DETERMINANTES_INICIAL = "Matriz inicial"
DETERMINANTES_COLUMNA = "Columna {columna} · pivote {valor}{intercambio}"
DETERMINANTES_INTERCAMBIO = " · con intercambio"
DETERMINANTES_DIAGONAL = "Producto diagonal"
DETERMINANTES_FINAL = "Resultado"
RESULTADO_CUENTA_PASOS = "{cantidad} pasos"
RESULTADO_INTERCAMBIOS = "{cantidad} intercambios"
RESULTADO_TIEMPO = "calculado en {segundos:.2f} s"
RESULTADO_INTERPRETACION = "¿Cómo interpretar este resultado?"
DETERMINANTES_INTERPRETACION = (
    "El determinante mide el factor de escala orientado. Si vale cero, A es singular; "
    "si es distinto de cero, A tiene inversa. Cofactores y eliminación obtienen el mismo valor exacto."
)
MODELOS_AYUDA = (
    "Recorre las fases y usa Explicar paso para consultar los datos del paso actual.",
    "Las comprobaciones usan la captura original y aritmética exacta; no son un segundo cálculo aproximado.",
)
MODELOS_FASES = ("Planteamiento", "Desarrollo", "Comprobación y resultado")
MODELOS_REDUCCION = "Reducción de A"
MODELOS_COMPROBACION = "Comprobación del modelo"
MODELOS_LEYENDA = ("planteamiento", "inicial", "pivote", "intercambio", "eliminacion", "normalizacion", "verificacion", "final")
LEONTIEF_INTERPRETACION = "Comprueba (I − C)x = d y el balance de cada sector. Hawkins-Simon indica viabilidad económica cuando su criterio es aplicable."
TRANSFORMACIONES_INTERPRETACION = "Los pivotes determinan el rango y la base de la imagen. Las variables libres determinan el núcleo; rango más nulidad es la dimensión del dominio."
RESULTADO_COPIAR = "Copiar resultado"
RESULTADO_COPIADO = "Resultado copiado al portapapeles"
RESULTADO_COPIAR_ERROR = "No se pudo copiar el resultado. Revisa los permisos del portapapeles y vuelve a intentarlo."
RESULTADO_CAMPOS_COPIABLES = (
    ("determinante", "Determinante"), ("permutacion", "P"), ("inferior", "L"), ("superior", "U"),
    ("solucion", "Solución"), ("matriz_resultado", "Resultado"), ("vector_resultado", "Vector"),
    ("coeficientes_texto", "Coeficientes"), ("solucion_parametrica", "Solución paramétrica"),
    ("vector_produccion", "Producción"), ("rango", "Rango"), ("nulidad", "Nulidad"),
    ("base_nucleo", "Base del núcleo"), ("base_imagen", "Base de la imagen"),
)
MODELOS_VISTA_PREVIA = "Vista previa de la captura"
MODELOS_HISTORIAL = "Últimos cálculos de esta sesión"
MODELOS_HISTORIAL_VACIO = "Aún no has calculado este modelo."
MODELOS_RESTAURAR = "Restaurar captura"
HISTORIAL_DETERMINANTE_CALCULADO = "Calculado"
HISTORIAL_DETERMINANTE_DETALLE = "det = {determinante}. Método: {metodo}"
HISTORIAL_FACTORIZACION_LU_CALCULADA = "Factorización calculada"
HISTORIAL_FACTORIZACION_LU_DETALLE = "rango {rango}"
CAPTURA_RECTANGULAR_AYUDA = "Pega desde Excel o un bloc de notas (tabuladores o comas). Máx. {limite}×{limite}."
CAPTURA_RECTANGULAR_RECORTADA = "La matriz supera el límite; se conservaron las primeras {limite} filas y columnas."
CAPTURA_PORTAPAPELES_ERROR = "No se pudo acceder al portapapeles. Comprueba los permisos y vuelve a intentarlo."
CAPTURA_RECTANGULAR_MATRIZ = "Matriz A"
CAPTURA_RECTANGULAR_PEGAR = "Pegar"
CAPTURA_RECTANGULAR_TOOLTIP = "Pegar matriz desde el portapapeles"
CAPTURA_RECTANGULAR_EJES = (("filas", "Filas"), ("columnas", "Columnas"))
CAPTURA_RECTANGULAR_ACCIONES = ((-1, "remove", "Quitar"), (1, "add", "Añadir"))
LU_TITULO = "Factorización LU"
LU_DESCRIPCION = "Descompón una matriz mediante pivoteo parcial."
LU_CONVENCION = "P registra los intercambios de filas, L guarda los multiplicadores con 1 en la diagonal y U es escalonada. La singularidad no impide factorizar."
LU_ORIENTACION = "Ingresa una matriz y pulsa Calcular factorización."
LU_VACIA = "Ingresa al menos un valor antes de calcular."
LU_CALCULAR = "Calcular factorización"
LU_DATOS = "Dimensiones: {filas} × {columnas} · Rango: {rango} · Convención: {convencion}"
LU_VEREDICTO = "LU = PA: {veredicto}"
LU_CORRECTO = "Correcto"
LU_INCORRECTO = "Incorrecto"
LU_LECTURAS = ("P registra los intercambios de filas.", "L contiene los multiplicadores de eliminación.", "U contiene la matriz escalonada.")
LU_AYUDA = ("Cómo leer esta factorización: sigue los pivotes y compara los factores con PA.",)
LU_FASES = ("Convención", "Eliminación con pivoteo parcial", "Factores", "Desarrollo de PA y comprobación")
LU_CUENTA_PASOS = "{cantidad} pasos"
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
