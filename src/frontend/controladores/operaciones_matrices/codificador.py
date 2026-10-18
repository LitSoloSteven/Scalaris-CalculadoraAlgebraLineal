"""Codificador JSON para estructuras matriciales y fraccionarias exactas."""
from fractions import Fraction
import json

from src.backend.modelos.matriz import Matriz


class CodificadorMatriz(json.JSONEncoder):
    """Serializa instancias de Matriz y Fraction a estructuras compatibles JSON."""

    def default(self, objeto):
        """Convierte matrices y fracciones a diccionarios y representaciones exactas."""
        if isinstance(objeto, Matriz):
            filas = objeto.filas
            columnas = objeto.columnas
            datos = objeto.datos
            return {
                "filas": filas,
                "columnas": columnas,
                "datos": datos,
            }
        if isinstance(objeto, Fraction):
            if objeto.denominator != 1:
                return f"{objeto.numerator}/{objeto.denominator}"
            return str(objeto.numerator)
        return super().default(objeto)
