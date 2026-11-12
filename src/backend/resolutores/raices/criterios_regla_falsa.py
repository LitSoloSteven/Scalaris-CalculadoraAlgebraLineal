"""Validación y métricas de criterios sobre filas de la secante."""
from .aritmetica_biseccion import ancho_intervalo
from .contrato_regla_falsa import IteracionReglaFalsa
from .criterios_biseccion import CriterioParada, validar_criterio

MOTIVOS_CRITERIO = {
    "residuo": "tolerancia_residuo",
    "ancho": "criterio_ancho_cumplido",
    "decimales": "criterio_decimales_cumplido",
    "relativo": "criterio_relativo_cumplido",
    "iteraciones": "iteraciones_solicitadas_completadas",
}


def validar_criterio_regla_falsa(valor: object, limite: int) -> CriterioParada:
    """Valida una solicitud explícita; lanza ValueError sin inferir un criterio decimal."""
    if valor is None:
        raise ValueError("Selecciona un criterio de parada.")
    return validar_criterio(valor, 0, limite)


def metrica_regla_falsa(criterio: CriterioParada, fila: IteracionReglaFalsa) -> float | int | None:
    """Devuelve la métrica interna; el ancho corresponde al intervalo posterior."""
    if criterio.tipo in ("ancho", "decimales"):
        return ancho_intervalo(*fila.intervalo_siguiente)
    valores = {"residuo": fila.residuo, "relativo": fila.error_relativo_porcentual,
               "iteraciones": fila.i}
    return valores[criterio.tipo]


def motivo_criterio_regla_falsa(criterio: CriterioParada, fila: IteracionReglaFalsa) -> str:
    """Compara sin redondear; los umbrales decimales conservan su fracción exacta."""
    metrica = metrica_regla_falsa(criterio, fila)
    cumplido = metrica == criterio.parametro if criterio.tipo == "iteraciones" else (
        metrica is not None and metrica < criterio.umbral)
    return MOTIVOS_CRITERIO[criterio.tipo] if cumplido else ""
