"""Mensajes y estados visibles de la herramienta de métodos iterativos."""

METODO_INICIAL = 'jacobi'
METODO_SECUENCIAL = 'gauss-seidel'
NOMBRES_METODOS = {METODO_INICIAL: 'Jacobi', METODO_SECUENCIAL: 'Gauss-Seidel'}
AYUDA_METODOS = {
    METODO_INICIAL: 'Cada ecuación usa los valores del vector anterior.',
    METODO_SECUENCIAL: 'Cada ecuación usa los valores ya actualizados en el mismo barrido y los anteriores para las incógnitas restantes.',
}
ESTADO_INICIAL = 'Escribe un sistema o carga el ejemplo.'
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
