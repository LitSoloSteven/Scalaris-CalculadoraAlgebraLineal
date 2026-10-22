"""Paquete de navegación, taxonomía y resolución de rutas de Scalaris."""

from src.frontend.navegacion.catalogo import (
    INICIO_HABILITADO,
    TITULO_PAGINA_INICIO,
    RUTA_INICIO,
    ORDEN_NAVEGACION_PLANA,
    PILARES,
    HERRAMIENTAS,
    ESCENAS_VISUALIZADOR,
)
from src.frontend.navegacion.consultas import (
    ruta_navegacion,
    predeterminado_elemento_clave,
    grupos_navegacion,
    enlace_elemento_navegacion,
    elementos_navegacion,
    pilar_por_ruta,
    pilar_de,
    ruta_de,
    herramienta_por_identificador,
    herramienta_por_ruta,
    herramientas_visibles,
)
from src.frontend.navegacion.modelo import RedireccionHeredada, ElementoNavegacion, Pilar, Herramienta
from src.frontend.navegacion.redirecciones import redirecciones_heredadas, ubicacion_redireccion

__all__ = [
    "INICIO_HABILITADO",
    "TITULO_PAGINA_INICIO",
    "RUTA_INICIO",
    "RedireccionHeredada",
    "ORDEN_NAVEGACION_PLANA",
    "ElementoNavegacion",
    "PILARES",
    "Pilar",
    "HERRAMIENTAS",
    "Herramienta",
    "ESCENAS_VISUALIZADOR",
    "ruta_navegacion",
    "predeterminado_elemento_clave",
    "redirecciones_heredadas",
    "grupos_navegacion",
    "enlace_elemento_navegacion",
    "elementos_navegacion",
    "pilar_por_ruta",
    "pilar_de",
    "ubicacion_redireccion",
    "ruta_de",
    "herramienta_por_identificador",
    "herramienta_por_ruta",
    "herramientas_visibles",
]
