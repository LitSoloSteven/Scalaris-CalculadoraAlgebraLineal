"""Mensajes y estados visibles de la herramienta de métodos iterativos."""

METODO_INICIAL = 'jacobi'
METODO_SECUENCIAL = 'gauss-seidel'
NOMBRES_METODOS = {METODO_INICIAL: 'Jacobi', METODO_SECUENCIAL: 'Gauss-Seidel'}
AYUDA_METODOS = {
    METODO_INICIAL: 'Cada ecuación usa los valores del vector anterior.',
    METODO_SECUENCIAL: 'Cada ecuación usa los valores ya actualizados en el mismo barrido y los anteriores para las incógnitas restantes.',
}
ESTADO_INICIAL = 'Escribe un sistema y sus parámetros para calcular.'
ESTADO_EDICION = 'Resuelve el sistema para actualizar el resultado.'
ESTADO_CALCULO = 'Calculando las iteraciones de {metodo}…'
EJEMPLO_CARGADO = 'Ejemplo cargado. Con sus parámetros iniciales, Jacobi alcanza la tolerancia en 6 barridos y Gauss-Seidel en 4.'
CAUSAS_PARADA = {
    'SOLUCION_EXACTA': 'Solución exacta',
    'TOLERANCIA_ALCANZADA': 'Tolerancia alcanzada',
    'MAXIMO_ITERACIONES': 'Máximo de iteraciones alcanzado',
    'LIMITE_ARITMETICO': 'Límite aritmético alcanzado',
    'DIAGONAL_NULA': 'Diagonal nula',
    'ENTRADA_INVALIDA': 'Revisa la captura',
}

PDF_ESTADOS_ITERATIVOS = {
    'SOLUCION_EXACTA': 'solución exacta',
    'TOLERANCIA_ALCANZADA': 'tolerancia alcanzada',
    'MAXIMO_ITERACIONES': 'máximo de iteraciones alcanzado',
    'LIMITE_ARITMETICO': 'límite aritmético alcanzado',
}
PDF_REGIONES_ITERATIVOS = {
    'metodos_iterativos-resumen': (
        'Resumen del Método Iterativo',
        'Se presenta el método usado, la causa de parada, el resultado exacto o aproximado, el residuo y la tolerancia.',
    ),
    'metodos_iterativos-tabla': (
        'Tabla de Iteraciones',
        'Se presentan los barridos completos confirmados con el vector obtenido, la norma del residuo y la norma del cambio.',
    ),
    'metodos_iterativos-resultado': (
        'Barrido Final del Procedimiento',
        'Se presenta el último barrido confirmado con la sustitución de las incógnitas.',
    ),
    'metodos_iterativos-procedimiento': (
        'Paso Visible del Procedimiento',
        'Se presenta únicamente el paso visible del procedimiento, sin recorrer los demás pasos.',
    ),
}
