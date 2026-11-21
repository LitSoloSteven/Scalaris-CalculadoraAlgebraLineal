"""Alias compatible del módulo de muestreo, incluido su punto de evaluación."""
import sys

from src.frontend.controladores.raices.compartido.exploracion import muestreo_raices

sys.modules[__name__] = muestreo_raices
