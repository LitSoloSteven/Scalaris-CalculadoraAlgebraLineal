"""Lectura independiente de controles para los trabajadores de modelos matriciales."""
from typing import Any
from src.frontend.textos_transformaciones import MODO_APLICACION


def capturar_leontief(vista: Any) -> dict:
    """Copia coeficientes, demanda y nombres de la vista; devuelve carga del controlador."""
    return {
        'matriz_coeficientes': [[entrada.value or '0' for entrada in fila]
                                for fila in vista.entradas_coeficientes],
        'vector_demanda': [entrada.value or '0' for entrada in vista.entradas_demanda],
        'nombres_sectores': [entrada.value.strip() or f'Sector {indice + 1}'
                             for indice, entrada in enumerate(vista.entradas_sectores)],
    }


def capturar_transformaciones(vista: Any) -> dict:
    """Copia la matriz y variables de la vista; devuelve carga del controlador."""
    variables = [entrada.value.strip() for entrada in vista.entradas_variables]
    captura = {
        'matriz_transformacion': [[vista.entradas_coeficientes[i][j].value or '0'
                                   for j in range(vista.columnas)] for i in range(vista.filas)],
        'nombres_variables': [variable or f'x{indice + 1}' for indice, variable in enumerate(variables)],
    }
    if getattr(vista, 'modo_transformacion', None) == MODO_APLICACION:
        captura.update(modo_transformacion=MODO_APLICACION, tipo_objeto=vista.tipo_objeto,
                       vector_original=[entrada.value or '0' for entrada in vista.entradas_vector_original])
    return captura
