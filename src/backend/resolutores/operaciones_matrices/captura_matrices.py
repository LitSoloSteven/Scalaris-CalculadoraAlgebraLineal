"""Captura exacta de colecciones matriciales sin dependencias de interfaz."""
from src.backend.modelos.matriz import Matriz
from .celdas_exactas import parsear_celda_exacta


def _validar_forma_matriz(nombre: str, datos_matriz: dict) -> tuple[int, int, list]:
    """Valida los campos obligatorios y tipos de una matriz en la carga."""
    if not isinstance(datos_matriz, dict):
        raise ValueError(f"Matriz '{nombre}': se esperaba un objeto con filas/columnas/datos.")
    filas = datos_matriz.get("filas")
    columnas = datos_matriz.get("columnas")
    datos = datos_matriz.get("datos")
    if not isinstance(filas, int) or isinstance(filas, bool) or filas <= 0:
        raise ValueError(f"Matriz '{nombre}': 'filas' debe ser un entero positivo.")
    if not isinstance(columnas, int) or isinstance(columnas, bool) or columnas <= 0:
        raise ValueError(f"Matriz '{nombre}': 'columnas' debe ser un entero positivo.")
    if not isinstance(datos, list):
        raise ValueError(f"Matriz '{nombre}': 'datos' debe ser una lista de filas.")
    if len(datos) != filas:
        raise ValueError(f"Matriz '{nombre}': 'datos' tiene {len(datos)} filas; se esperaban {filas}.")
    return filas, columnas, datos


def _parsear_filas_matriz(nombre: str, datos: list, columnas: int) -> list[list]:
    """Convierte las celdas a fracciones exactas y señala coordenadas inválidas."""
    filas_parseadas = []
    for indice_fila, fila in enumerate(datos):
        if not isinstance(fila, list):
            raise ValueError(f"Matriz '{nombre}': fila {indice_fila + 1} no es una lista.")
        if len(fila) != columnas:
            raise ValueError(f"Matriz '{nombre}': fila {indice_fila + 1} tiene {len(fila)} columnas; se esperaban {columnas}.")
        fila_actual = []
        for indice_columna, celda in enumerate(fila):
            coordenada = f"Matriz {nombre}, celda [{indice_fila + 1},{indice_columna + 1}]"
            fila_actual.append(parsear_celda_exacta(celda, coordenada, vacio_como_cero=True))
        filas_parseadas.append(fila_actual)
    return filas_parseadas


def obtener_diccionario_matrices(datos_matrices: dict) -> dict[str, Matriz]:
    """Construye matrices exactas desde cargas crudas; lanza ValueError si son inválidas."""
    if not isinstance(datos_matrices, dict):
        raise ValueError("La carga debe contener un diccionario de matrices.")
    if not datos_matrices:
        raise ValueError("No se recibió ninguna matriz para evaluar.")
    matrices = {}
    for nombre, datos_matriz in datos_matrices.items():
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("Cada matriz debe tener un nombre no vacío.")
        filas, columnas, datos = _validar_forma_matriz(nombre, datos_matriz)
        datos_parseados = _parsear_filas_matriz(nombre, datos, columnas)
        matrices[nombre] = Matriz(filas=filas, columnas=columnas, datos=datos_parseados)
    return matrices
