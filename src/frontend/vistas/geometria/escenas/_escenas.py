"""Constructores públicos de figuras para las escenas geométricas."""
from src.frontend.vistas.geometria.figuras._figura_rectas_planos import construir_figura_rectas_planos
from src.frontend.vistas.geometria.figuras._figura_vectores import construir_figura_vectores
from src.frontend.vistas.geometria.figuras._figura_combinacion import construir_figura_combinacion

__all__ = [
    'construir_figura_rectas_planos',
    'construir_figura_vectores',
    'construir_figura_combinacion',
]
