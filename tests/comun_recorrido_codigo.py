"""Recorrido de archivos y nodos compartido por auditorías estáticas."""
import ast
import os
from pathlib import Path


def recorrer_archivos_codigo(carpetas, extensiones):
    """Recorre las carpetas indicadas y conserva el orden y las extensiones de búsqueda."""
    for carpeta in carpetas:
        yield from _recorrer_carpeta(carpeta, extensiones)


def _recorrer_carpeta(carpeta, extensiones):
    for raiz, _, archivos in os.walk(carpeta):
        for nombre in archivos:
            if nombre.endswith(extensiones):
                yield Path(raiz) / nombre


def recorrer_lineas_codigo(rutas):
    """Entrega ruta, número de línea y contenido de cada archivo solicitado."""
    for ruta in rutas:
        with ruta.open(encoding="utf-8") as archivo:
            for numero, linea in enumerate(archivo, 1):
                yield ruta, numero, linea


def pares_padre_hijo(arbol):
    """Entrega cada relación directa entre un nodo sintáctico y su padre."""
    for padre in ast.walk(arbol):
        for hijo in ast.iter_child_nodes(padre):
            yield padre, hijo


def nombres_de_asignaciones(arbol):
    """Recoge destinos que son nombres directos en asignaciones ordinarias."""
    return [destino for nodo in ast.walk(arbol) if isinstance(nodo, ast.Assign)
            for destino in nodo.targets if isinstance(destino, ast.Name)]


def cadena_estatica(nodo):
    """Extrae un literal o la parte estática de una cadena interpolada, si existe."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    if isinstance(nodo, ast.JoinedStr):
        return "".join(_parte_estatica(valor) for valor in nodo.values)
    return None


def _parte_estatica(nodo):
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    return ""
