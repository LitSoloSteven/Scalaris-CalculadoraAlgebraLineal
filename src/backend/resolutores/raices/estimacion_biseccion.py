"""Estimación exacta de filas ideales para condiciones geométricas estrictas."""
from dataclasses import asdict, dataclass
from fractions import Fraction

from .aritmetica_biseccion import cota_intervalo
from .contrato_biseccion import EntradaBiseccion, validar_entrada

_HIPOTESIS = "La estimación supone ausencia de ceros evaluados y de interrupciones numéricas."


@dataclass(frozen=True)
class EstimacionBiseccion:
    """Número previsto de filas, aviso de límite y restricciones de la predicción."""

    filas_previstas: int | None
    supera_limite: bool
    advertencias: tuple[str, ...]


def estimar_iteraciones(entrada: EntradaBiseccion) -> EstimacionBiseccion:
    """Estima filas sin evaluar f; lanza ValueError ante entrada o intervalo no representable."""
    if not isinstance(entrada, EntradaBiseccion):
        raise ValueError("La estimación requiere una entrada de bisección.")
    entrada = validar_entrada(asdict(entrada))
    cota_intervalo(entrada.extremo_izquierdo, entrada.extremo_derecho)
    criterio = entrada.criterio_activo
    if criterio.tipo in {"relativo", "residuo"}:
        return EstimacionBiseccion(None, False, ("Este criterio no permite estimar las filas solo con el ancho.",))
    if criterio.tipo == "iteraciones":
        filas = criterio.parametro
    else:
        ancho = Fraction(entrada.extremo_derecho) - Fraction(entrada.extremo_izquierdo)
        filas = _filas_geometricas(ancho, Fraction(criterio.umbral))
    supera_limite = filas > entrada.limite_iteraciones
    advertencias = (_HIPOTESIS,)
    if supera_limite:
        advertencias += ("Las filas previstas superan el límite de iteraciones elegido.",)
    return EstimacionBiseccion(filas, supera_limite, advertencias)


def _filas_geometricas(ancho: Fraction, umbral: Fraction) -> int:
    cociente = ancho / umbral
    particiones = max(0, cociente.numerator.bit_length() - cociente.denominator.bit_length())
    while cociente >= 1 << particiones:
        particiones += 1
    while particiones > 0 and cociente < 1 << (particiones - 1):
        particiones -= 1
    return 1 + particiones
