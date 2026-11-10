"""Alias compatible del módulo de muestreo, incluido su punto de evaluación."""
import sys

from src.frontend.controladores import muestreo_raices

sys.modules[__name__] = muestreo_raices
