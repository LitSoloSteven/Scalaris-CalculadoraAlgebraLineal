"""Prioridad de criterios y estancamiento en una fila de regla falsa."""
from .contrato_regla_falsa import EntradaReglaFalsa, IteracionReglaFalsa
from .criterios_biseccion import CriterioParada
from .criterios_regla_falsa import motivo_criterio_regla_falsa
from .traza_regla_falsa import crear_iteracion_estancamiento


def decidir_parada_regla_falsa(
    entrada: EntradaReglaFalsa, fila: IteracionReglaFalsa,
    previo: float | None, criterio: CriterioParada | None = None,
) -> tuple[IteracionReglaFalsa, str]:
    """Devuelve fila y cierre; sin criterio conserva la precedencia clásica."""
    if fila.valor_aproximacion == 0:
        return fila, "raiz_en_aproximacion"
    activo = criterio or CriterioParada("residuo", entrada.tolerancia)
    estancado = fila.aproximacion in (fila.extremo_izquierdo, fila.extremo_derecho, previo)
    motivo = motivo_criterio_regla_falsa(activo, fila)
    if motivo and (not estancado or activo.tipo in ("residuo", "ancho", "decimales")):
        return fila, motivo
    if estancado:
        extremos = (fila.extremo_izquierdo, fila.extremo_derecho, fila.valor_izquierdo, fila.valor_derecho)
        return crear_iteracion_estancamiento(
            fila.i, extremos, (fila.aproximacion, fila.valor_aproximacion),
            (fila.extremo_izquierdo, fila.extremo_derecho)), "estancamiento_numerico"
    return fila, "limite_iteraciones" if fila.i == entrada.limite_iteraciones else ""
