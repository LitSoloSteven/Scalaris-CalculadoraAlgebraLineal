"""Codificador JSON para estructuras matriciales y fraccionarias exactas."""
from collections.abc import Mapping
from fractions import Fraction
import json

from src.backend.modelos.conversion_fracciones import texto_fraccion_exacta
from src.backend.modelos.matriz import Matriz


class CodificadorMatriz(json.JSONEncoder):
    """Serializa instancias de Matriz y Fraction a estructuras compatibles JSON."""

    def default(self, objeto):
        """Convierte matrices, mapas inmutables y fracciones a estructuras exactas."""
        if isinstance(objeto, Matriz):
            filas = objeto.filas
            columnas = objeto.columnas
            datos = objeto.datos
            return {
                "filas": filas,
                "columnas": columnas,
                "datos": datos,
            }
        if isinstance(objeto, Mapping):
            return dict(objeto)
        if isinstance(objeto, Fraction):
            return texto_fraccion_exacta(objeto)
        return super().default(objeto)
