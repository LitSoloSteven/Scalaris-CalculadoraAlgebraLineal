"""Mensajes y estados visibles de la herramienta de métodos iterativos."""

ESTADO_INICIAL = 'Escribe un sistema o carga el ejemplo de Jacobi.'
ESTADO_EDICION = 'Resuelve el sistema para actualizar el resultado.'
ESTADO_CALCULO = 'Calculando las iteraciones de Jacobi…'
CAUSAS_PARADA = {
    'SOLUCION_EXACTA': 'Solución exacta',
    'TOLERANCIA_ALCANZADA': 'Tolerancia alcanzada',
    'MAXIMO_ITERACIONES': 'Máximo de iteraciones alcanzado',
    'LIMITE_ARITMETICO': 'Límite aritmético alcanzado',
    'DIAGONAL_NULA': 'Diagonal nula',
    'ENTRADA_INVALIDA': 'Revisa la captura',
}
