"""Módulo de geometría lineal y analítica para el backend."""
from src.backend.geometria.clasificacion import (
    clasificar_ecuacion,
    detectar_paralelismo,
    son_proporcionales,
)
from src.backend.geometria.conjunto_solucion import (
    ConjuntoSolucion,
    TipoSolucionGeometria,
    clasificar_conjunto_solucion,
    construir_conjunto_desde_gauss,
    construir_conjunto_desde_parametros,
    obtener_parametros_solucion,
    validar_solucion_parametrica,
)
from src.backend.geometria.planos import calcular_geometria_plano
from src.backend.geometria.recorte import (
    calcular_rango_automatico,
    recortar_recta_a_caja,
)

__all__ = [
    "ConjuntoSolucion",
    "TipoSolucionGeometria",
    "calcular_geometria_plano",
    "calcular_rango_automatico",
    "clasificar_conjunto_solucion",
    "clasificar_ecuacion",
    "construir_conjunto_desde_gauss",
    "construir_conjunto_desde_parametros",
    "detectar_paralelismo",
    "obtener_parametros_solucion",
    "recortar_recta_a_caja",
    "son_proporcionales",
    "validar_solucion_parametrica",
]
