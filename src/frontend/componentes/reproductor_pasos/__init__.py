"""API pública del reproductor interactivo de pasos."""
from __future__ import annotations

from src.frontend.componentes.reproductor_pasos.catalogo import (
    CATALOGO_TIPOS,
    DIMENSION_MAXIMA_FRACCIONES_APILADAS,
    VELOCIDADES_AUTOREPRODUCCION,
    html_sugerencia_tipo,
)
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.html_tablas import (
    etiqueta_variable_html,
    formatear_decimal,
    formatear_valor,
    html_tabla_aumentada,
    html_tabla_matriz,
)
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.componentes.reproductor_pasos.reproductor import ReproductorPasos

__all__ = [
    "CATALOGO_TIPOS",
    "GrupoReproductor",
    "PasoReproductor",
    "ReproductorPasos",
    "DIMENSION_MAXIMA_FRACCIONES_APILADAS",
    "VELOCIDADES_AUTOREPRODUCCION",
    "etiqueta_variable_html",
    "formatear_decimal",
    "formatear_valor",
    "html_sugerencia_tipo",
    "html_tabla_aumentada",
    "html_tabla_matriz",
    "renderizar_latex",
]
