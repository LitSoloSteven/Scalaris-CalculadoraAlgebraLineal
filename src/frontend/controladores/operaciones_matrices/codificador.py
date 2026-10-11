"""Codificador JSON para estructuras matriciales y fraccionarias exactas."""
from fractions import Fraction
import json

from src.backend.modelos.matriz import Matriz


class CodificadorMatriz(json.JSONEncoder):
    """Serializa instancias de Matrix, Matriz y Fraction a estructuras compatibles JSON."""

    def default(self, obj):
        """Convierte matrices y fracciones a diccionarios y representaciones exactas."""
        if isinstance(obj, Matriz) or getattr(obj, "__class__", None).__name__ in ("Matrix", "Matriz"):
            filas = getattr(obj, "filas", getattr(obj, "rows", 0))
            columnas = getattr(obj, "columnas", getattr(obj, "cols", 0))
            datos = getattr(obj, "datos", getattr(obj, "data", []))
            return {
                "rows": filas,
                "cols": columnas,
                "data": datos,
                "filas": filas,
                "columnas": columnas,
                "datos": datos,
            }
        if isinstance(obj, Fraction):
            if obj.denominator != 1:
                return f"{obj.numerator}/{obj.denominator}"
            return str(obj.numerator)
        return super().default(obj)
