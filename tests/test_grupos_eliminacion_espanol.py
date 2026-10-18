"""Caracterización del estado compartido de agrupación tras normalizar pivotes."""
from src.backend.modelos.matriz import Matriz
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion


def test_normalizacion_cierra_columna_antes_de_operacion_no_clasificada():
    """Un paso posterior pertenece a normalización y no a la columna ya cerrada."""
    inicial = Matriz(1, 2, [[2, 6]])
    normalizada = Matriz(1, 2, [[1, 3]])
    entradas = [
        {"descripcion": "Matriz inicial aumentada [A|b]:", "matriz": inicial},
        {"descripcion": "Pivote seleccionado en Fila 1, Columna 1 (valor = 2)", "matriz": inicial},
        {"descripcion": "Normalizar pivote: Fila 1 = Fila 1 / 2", "matriz": normalizada},
        {"descripcion": "Resultado comprobado", "matriz": normalizada},
    ]
    pasos, grupos, estadisticas = agrupar_pasos_eliminacion(entradas, 1, "SOLUCION_UNICA", contexto="sistema", metodo="gauss")
    assert [grupo["indices_pasos"] for grupo in grupos] == [[0], [1], [2, 3]]
    assert [paso["indice_grupo"] for paso in pasos] == [0, 1, 2, 2]
    assert estadisticas == {"total": 4, "pivotes": 1, "intercambios": 0, "eliminaciones": 0, "normalizaciones": 1}
