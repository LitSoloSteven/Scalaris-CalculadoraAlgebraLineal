"""Catálogo centralizado de textos y mensajes de interfaz de Scalaris."""

MENSAJE_ANTI_REBOTE_GLOSA = "Espera un momento antes de enviar otra pregunta."
MENSAJE_ENTRADA_NUMERICA = "Solo se admiten números, fracciones y decimales."

PDF_EXPORTAR = "Exportar PDF"
PDF_PORTADA_TITULO = "Datos de la portada"
PDF_CAMPOS = {"nombre": "Nombre completo", "fecha": "Fecha", "docente": "Docente", "grupo": "Número de grupo"}
PDF_AFILIACION = "UAM"
PDF_MARCA = "Scalaris"
PDF_TITULO_RESULTADO = "Resultado de {herramienta}"
PDF_HERRAMIENTAS = {
    "sistemas": "Sistemas de ecuaciones lineales", "vectores": "Operaciones con vectores",
    "matrices": "Operaciones con matrices", "inversa": "Matriz inversa",
    "determinantes": "Determinantes", "lu": "Factorización LU",
    "leontief": "Modelo de Leontief", "transformaciones": "Transformaciones lineales",
    "bases": "Conversor de bases", "romanos": "Números romanos",
    "visualizador": "Visualizador geométrico",
}
PDF_GRUPO = "Grupo {grupo}"
PDF_DOCENTE = "Docente: {docente}"
PDF_CANCELAR = "Cancelar"
PDF_GENERAR = "Generar PDF"
PDF_CARGANDO = "Preparando las capturas y el PDF. Espera un momento."
PDF_CAPTURANDO = "Capturando el resultado…"
PDF_GENERANDO = "Generando el documento…"
PDF_ERROR_CAPTURA = "No pudimos capturar el resultado. Cierra la portada, comprueba que el resultado esté visible y vuelve a intentarlo."
PDF_ERROR_GENERACION = "No pudimos generar el PDF. Revisa los datos de la portada y vuelve a intentarlo."
PDF_ERROR_OBSOLETO = "Los datos cambiaron. Cierra la portada y vuelve a calcular antes de exportar."
PDF_ERROR_IMAGEN = "Las capturas no son válidas o superan los límites. Reduce el resultado visible y vuelve a exportar."
PDF_ERROR_GLIFOS = "Hay caracteres que la fuente del PDF no admite. Escribe los datos de la portada con caracteres latinos y vuelve a intentarlo."
PDF_ERROR_CAMPO = "Escribe {campo} para generar la portada."
PDF_ERRORES_VACIOS = {"nombre": "tu nombre completo", "docente": "el nombre del docente", "grupo": "el número de grupo"}
PDF_ERROR_LONGITUD = "Usa como máximo {limite} caracteres en este campo."
PDF_ERROR_GRUPO = "Usa solo letras y números, sin espacios, en el número de grupo."
PDF_ERROR_FECHA = "Selecciona una fecha válida para generar la portada."
PDF_ERROR_CARACTERES = "Usa caracteres latinos legibles, sin controles ni símbolos especiales."
PDF_MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
PDF_FECHA = "{dia} de {mes} de {anio}"
PDF_SECCION = "Resultado"
PDF_FIGURA = "Figura {numero}"
PDF_NOTA = "Nota."
PDF_CITA = "Como se muestra en la Figura {numero}, {descripcion}"
PDF_AVISO_REDUCCION = "La figura se redujo para ajustarse al alto útil de la página. Amplía el PDF para revisar sus detalles."
PDF_ENTRADA = ("Datos Introducidos", "Se presentan los datos introducidos para el cálculo exportado.")
PDF_PASO_INTERMEDIO = ("Paso Intermedio {numero}", "Se presenta una captura intermedia del procedimiento calculado.")
PDF_PASO_ORIGINAL = "Paso {numero} de {total}"
PDF_ETIQUETAS_ENTRADA = {
    "A": "Matriz A", "b": "Vector b", "datos": "Datos", "matriz_a": "Matriz A",
    "matrices": "Matrices", "expresion": "Expresión", "dimension": "Dimensión",
    "metodo": "Método", "modo": "Modo", "homogeneo": "Sistema homogéneo",
    "ecuaciones": "Ecuaciones", "vectores": "Vectores", "orientacion": "Orientación",
    "operacion": "Operación", "escalar": "Escalar", "suma_resta": "Expresión vectorial",
    "estricto": "Modo estricto", "valor": "Valor", "base_origen": "Base de origen",
    "base_destino": "Base de destino", "a": "Primer operando",
    "matriz_coeficientes": "Matriz de coeficientes", "vector_demanda": "Demanda",
    "nombres_sectores": "Sectores", "matriz_transformacion": "Matriz de transformación",
    "nombres_variables": "Variables", "escena": "Escena", "carga": "Datos de la escena",
    "vector_b": "Vector b", "objetivo": "Vector objetivo",
}
PDF_BOOLEANOS = {True: "Sí", False: "No"}
PDF_SEGUNDO_OPERANDO = "Segundo operando"
PDF_VERIFICACIONES = ("Comprobaciones del Resultado", "Se presentan las comprobaciones entregadas por el procedimiento calculado.")
PDF_REGIONES_SISTEMAS = {
    "sistemas-resumen": ("Clasificación y Solución del Sistema", "Se presenta la clasificación y la solución que muestra el resultado calculado."),
    "sistemas-procedimiento": ("Paso Visible del Procedimiento", "Se presenta únicamente el paso visible del procedimiento, sin recorrer los demás pasos."),
}
PDF_DESCRIPCION_ESTADO = " Estado del resultado: {estado}."
PDF_ESTADOS_SISTEMAS = {"SOLUCION_UNICA": "solución única", "SOLUCIONES_INFINITAS": "infinitas soluciones", "SIN_SOLUCION": "sin solución"}
PDF_ESTADOS_ALGEBRA = {
    "EXITO": "cálculo completado", "SINGULAR": "matriz singular",
    "UNICA": "combinación única", "INFINITA": "infinitas combinaciones",
    "SIN_SOLUCION": "sin solución", "SOLUCIONES_INFINITAS": "infinitas soluciones",
}
PDF_PROCEDIMIENTO = ("Paso Visible del Procedimiento", "Se presenta únicamente el paso visible del procedimiento, sin recorrer los demás pasos.")
PDF_REGIONES_ALGEBRA = {
    "vectores": {
        "vectores-resumen": ("Estado de la Operación Vectorial", "Se presenta el estado de la operación con vectores calculada."),
        "vectores-solucion": ("Solución de la Operación Vectorial", "Se presenta el vector resultante, los coeficientes o el análisis de independencia que muestra la herramienta."),
        "vectores-procedimiento": PDF_PROCEDIMIENTO,
    },
    "matrices": {
        "matrices-resumen": ("Estado de la Expresión Matricial", "Se presenta el estado de la evaluación matricial."),
        "matrices-resultado": ("Matriz Resultante", "Se presenta la matriz final que muestra la herramienta."),
        "matrices-procedimiento": PDF_PROCEDIMIENTO,
    },
    "inversa": {
        "inversa-resumen": ("Estado de la Matriz Inversa", "Se presenta la clasificación de la matriz y el determinante mostrado."),
        "inversa-resultado": ("Resultado de la Inversión", "Se presenta la matriz inversa o la matriz evaluada cuando es singular."),
        "inversa-comprobaciones": ("Comprobaciones de la Inversa", "Se presentan las comprobaciones visibles entregadas por el cálculo."),
        "inversa-procedimiento": PDF_PROCEDIMIENTO,
    },
    "determinantes": {
        "determinantes-resumen": ("Valor del Determinante", "Se presenta el determinante y las métricas del cálculo."),
        "determinantes-procedimiento": PDF_PROCEDIMIENTO,
    },
    "lu": {
        "lu-resumen": ("Estado de la Factorización", "Se presenta el estado, las dimensiones y el rango de la factorización."),
        "lu-factores": ("Factores de la Matriz", "Se presentan los factores de permutación, triangular inferior y triangular superior, y su comprobación."),
        "lu-procedimiento": PDF_PROCEDIMIENTO,
    },
    "leontief": {
        "leontief-resumen": ("Resultado del Modelo de Leontief", "Se presenta el estado del modelo y la producción calculada cuando existe."),
        "leontief-analisis": ("Análisis del Modelo de Leontief", "Se presenta la condición de Hawkins-Simon y el análisis sectorial visible cuando existe."),
        "leontief-procedimiento": PDF_PROCEDIMIENTO,
    },
    "transformaciones": {
        "transformaciones-resumen": ("Propiedades de la Transformación", "Se presentan el rango, la nulidad y las propiedades de la transformación."),
        "transformaciones-bases": ("Núcleo e Imagen", "Se presentan las bases del núcleo y de la imagen entregadas por el cálculo."),
        "transformaciones-procedimiento": PDF_PROCEDIMIENTO,
    },
}
PDF_ESTADOS_POR_HERRAMIENTA = {
    "sistemas": PDF_ESTADOS_SISTEMAS,
    "vectores": {clave: PDF_ESTADOS_ALGEBRA[clave] for clave in ("EXITO", "UNICA", "INFINITA", "SIN_SOLUCION")},
    "matrices": {"EXITO": PDF_ESTADOS_ALGEBRA["EXITO"]},
    "inversa": {clave: PDF_ESTADOS_ALGEBRA[clave] for clave in ("EXITO", "SINGULAR")},
    "determinantes": {"EXITO": PDF_ESTADOS_ALGEBRA["EXITO"]},
    "lu": {"EXITO": PDF_ESTADOS_ALGEBRA["EXITO"]},
    "leontief": {clave: PDF_ESTADOS_ALGEBRA[clave] for clave in ("EXITO", "SINGULAR", "SIN_SOLUCION", "SOLUCIONES_INFINITAS")},
    "transformaciones": {"EXITO": PDF_ESTADOS_ALGEBRA["EXITO"]},
    "bases": {"EXITO": PDF_ESTADOS_ALGEBRA["EXITO"]},
    "romanos": {"EXITO": PDF_ESTADOS_ALGEBRA["EXITO"]},
    "visualizador": {"EXITO": PDF_ESTADOS_ALGEBRA["EXITO"]},
}
PDF_REGIONES_UTILIDADES = {
    "bases": {
        "bases-resultado": ("Conversión Entre Bases", "Se presentan las representaciones del número en las bases que muestra la herramienta."),
        "bases-procedimiento": PDF_PROCEDIMIENTO,
    },
    "romanos": {
        "romanos-resultado": ("Operación con Números Romanos", "Se presentan los operandos, la operación y el resultado romano calculado."),
        "romanos-procedimiento": PDF_PROCEDIMIENTO,
    },
    "visualizador": {
        "visualizador-resumen": ("Datos de la Escena Geométrica", "Se presentan los datos y el resumen de la escena que muestra el visualizador."),
        "visualizador-figura": ("Escena Geométrica Visible", "Se presenta la figura visible con sus trazas, encuadre y cámara actuales en tema claro."),
    },
}
PDF_REGIONES_POR_HERRAMIENTA = {
    "sistemas": PDF_REGIONES_SISTEMAS, **PDF_REGIONES_ALGEBRA, **PDF_REGIONES_UTILIDADES,
}
PDF_REGIONES_OBLIGATORIAS = {
    "bases": ("bases-resultado",), "romanos": ("romanos-resultado",),
    "visualizador": ("visualizador-resumen", "visualizador-figura"),
}

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
DETERMINANTES_ESTADO_NO_NULO = "Determinante no nulo"
DETERMINANTES_ESTADO_NULO = "Determinante nulo"
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
PASOS_AYUDA_TITULO = "¿Cómo leer los pasos?"
PASOS_INDICE_TITULO = "Índice de pasos por fases"
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

TRANSFERENCIA_MATRIZ_TITULO = "Llevar esta matriz a"
TRANSFERENCIA_MATRIZ_CAPTURADA = "Matriz {nombre} del cálculo"
TRANSFERENCIA_MATRIZ_CARGADA = "Cargamos {matriz} ({filas}×{columnas}) desde {origen}. {orientacion}"
TRANSFERENCIA_DIMENSION_MINIMA = "Esta herramienta necesita una matriz de al menos {minimo}×{minimo}. Captura una matriz compatible."
TRANSFERENCIA_ORIENTACIONES = {
    "inversa": ("A", "Presiona Calcular inversa para ver A⁻¹."),
    "determinantes": ("A", "Presiona Calcular determinante para obtener el resultado."),
    "factorizacion_lu": ("A", "Presiona Calcular factorización para obtener los factores."),
    "sistemas": ("A", "El vector b está vacío: complétalo y presiona Resolver."),
    "matrices": ("A", "Escribe una expresión y presiona Evaluar."),
    "transformaciones": ("A", "Presiona Analizar para estudiar la transformación."),
    "leontief": ("C", "La demanda está vacía: complétala y presiona Calcular."),
}
